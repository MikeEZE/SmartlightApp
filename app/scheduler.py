"""
Scheduler for automating light control
"""

import logging
import threading
import time
import uuid
from datetime import datetime, timedelta
from PySide6.QtCore import QObject, Signal, QTimer

from .constants import APP_NAME


logger = logging.getLogger(APP_NAME)


class SchedulerService(QObject):
    """
    Service for scheduling automatic light control actions
    """
    
    # Signals
    schedule_triggered = Signal(str)  # Schedule ID
    schedule_updated = Signal()
    
    def __init__(self, light_manager, config_manager):
        """Initialize scheduler with light manager and config manager"""
        super().__init__()
        self.light_manager = light_manager
        self.config_manager = config_manager
        self.schedules = {}  # Schedule ID -> schedule info
        self.stop_event = threading.Event()
        self.scheduler_thread = None
        self.check_timer = QTimer(self)
        
        # Load saved schedules
        self._load_schedules()
        
        # Start scheduler thread
        self._start_scheduler()
    
    def _load_schedules(self):
        """Load schedules from configuration"""
        schedule_list = self.config_manager.get_schedules()
        
        for schedule in schedule_list:
            if 'id' in schedule:
                self.schedules[schedule['id']] = schedule
        
        logger.info(f"Loaded {len(self.schedules)} schedules")
    
    def _start_scheduler(self):
        """Start the scheduler thread"""
        self.stop_event.clear()
        self.scheduler_thread = threading.Thread(
            target=self._scheduler_loop,
            daemon=True
        )
        self.scheduler_thread.start()
        
        # Set up timer to check schedules every minute in the UI thread
        self.check_timer.timeout.connect(self._check_schedules)
        self.check_timer.start(60000)  # 1 minute
        
        logger.info("Scheduler started")
    
    def stop(self):
        """Stop the scheduler thread"""
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            self.stop_event.set()
            self.scheduler_thread.join(timeout=1.0)
            self.check_timer.stop()
            logger.info("Scheduler stopped")
    
    def _scheduler_loop(self):
        """
        Main scheduler loop that runs in a background thread
        Checks for schedules to trigger every minute
        """
        while not self.stop_event.is_set():
            try:
                self._process_schedules()
            except Exception as e:
                logger.error(f"Error in scheduler: {str(e)}")
            
            # Sleep until the next minute
            now = datetime.now()
            next_minute = now.replace(second=0, microsecond=0) + timedelta(minutes=1)
            sleep_seconds = (next_minute - now).total_seconds()
            
            # Sleep in small increments to check for stop event
            for _ in range(int(sleep_seconds / 0.2)):
                if self.stop_event.is_set():
                    break
                time.sleep(0.2)
    
    def _process_schedules(self):
        """Process all schedules and trigger those that should run now"""
        now = datetime.now()
        
        for schedule_id, schedule in self.schedules.items():
            if self._should_trigger_schedule(schedule, now):
                self._trigger_schedule(schedule_id)
    
    def _should_trigger_schedule(self, schedule, now):
        """
        Check if a schedule should be triggered
        
        Args:
            schedule: Schedule information dictionary
            now: Current datetime
            
        Returns:
            bool: True if schedule should trigger, False otherwise
        """
        # Skip disabled schedules
        if not schedule.get('enabled', True):
            return False
        
        # Check if time matches
        if not self._time_matches(schedule, now):
            return False
        
        # Check if day matches (if days are specified)
        if 'days' in schedule and not self._day_matches(schedule, now):
            return False
        
        # Check if date matches (if specific date is set)
        if 'date' in schedule and not self._date_matches(schedule, now):
            return False
        
        # Check last run time to avoid duplicate triggers
        last_run = schedule.get('last_run')
        if last_run:
            last_datetime = datetime.fromisoformat(last_run)
            if now - last_datetime < timedelta(minutes=1):
                return False
        
        return True
    
    def _time_matches(self, schedule, now):
        """Check if the current time matches schedule time"""
        if 'time' not in schedule:
            return False
        
        schedule_time = schedule['time']
        hour, minute = map(int, schedule_time.split(':'))
        
        return now.hour == hour and now.minute == minute
    
    def _day_matches(self, schedule, now):
        """Check if the current day matches schedule days"""
        days = schedule['days']
        weekday = now.weekday()  # 0-6 (Monday to Sunday)
        
        # Convert to consistent format
        if isinstance(days, list):
            return weekday in days
        elif isinstance(days, str):
            if days == 'weekdays':
                return 0 <= weekday <= 4  # Monday to Friday
            elif days == 'weekend':
                return weekday >= 5  # Saturday or Sunday
            elif days == 'all':
                return True
        
        return False
    
    def _date_matches(self, schedule, now):
        """Check if the current date matches a specific date"""
        if 'date' not in schedule:
            return True  # No date restriction
        
        schedule_date = schedule['date']
        schedule_datetime = datetime.fromisoformat(schedule_date)
        
        return (now.year == schedule_datetime.year and 
                now.month == schedule_datetime.month and 
                now.day == schedule_datetime.day)
    
    def _trigger_schedule(self, schedule_id):
        """
        Execute actions for a triggered schedule
        
        Args:
            schedule_id: ID of the schedule to trigger
        """
        schedule = self.schedules.get(schedule_id)
        if not schedule:
            logger.error(f"Cannot find schedule {schedule_id}")
            return
        
        logger.info(f"Triggering schedule: {schedule.get('name', schedule_id)}")
        
        # Update last run time
        schedule['last_run'] = datetime.now().isoformat()
        self.config_manager.add_schedule(schedule)
        
        # Process actions
        actions = schedule.get('actions', [])
        for action in actions:
            self._execute_action(action)
        
        # Emit signal
        self.schedule_triggered.emit(schedule_id)
    
    def _execute_action(self, action):
        """
        Execute a single schedule action
        
        Args:
            action: Action dictionary
        """
        action_type = action.get('type')
        target_type = action.get('target_type')
        target_id = action.get('target_id')
        state = action.get('state', {})
        
        logger.debug(f"Executing action: {action_type} on {target_type} {target_id}")
        
        try:
            if action_type == 'set_state':
                if target_type == 'light':
                    # Action for a single light
                    protocol, light_id = action.get('target_id').split('/')
                    self.light_manager.set_light_state(protocol, light_id, state)
                    
                elif target_type == 'group':
                    # Action for a group
                    self.light_manager.set_group_state(target_id, state)
                    
                elif target_type == 'all':
                    # Action for all lights
                    on_state = state.get('on')
                    if on_state is not None:
                        self.light_manager.set_all_lights(on_state)
        
        except Exception as e:
            logger.error(f"Error executing schedule action: {str(e)}")
    
    def _check_schedules(self):
        """
        Check for schedule triggers (in UI thread)
        This is a lightweight version that just updates the UI
        """
        now = datetime.now()
        
        for schedule_id, schedule in self.schedules.items():
            # Check if schedule is due in the next minute
            if self._should_trigger_soon(schedule, now):
                # Update UI to show schedule is about to trigger
                self.schedule_updated.emit()
    
    def _should_trigger_soon(self, schedule, now):
        """Check if schedule will trigger in the next minute"""
        if not schedule.get('enabled', True):
            return False
        
        if 'time' not in schedule:
            return False
        
        # Parse schedule time
        hour, minute = map(int, schedule['time'].split(':'))
        
        # Check if time is within the next minute
        target_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        time_diff = target_time - now
        
        return 0 <= time_diff.total_seconds() < 60
    
    def get_schedules(self):
        """
        Get all schedules
        
        Returns:
            dict: Schedule ID -> schedule info
        """
        return self.schedules
    
    def get_schedule(self, schedule_id):
        """
        Get a specific schedule
        
        Args:
            schedule_id: Schedule ID
            
        Returns:
            dict: Schedule information or None if not found
        """
        return self.schedules.get(schedule_id)
    
    def create_schedule(self, name, time, actions, days=None, date=None, enabled=True):
        """
        Create a new schedule
        
        Args:
            name: Schedule name
            time: Time in "HH:MM" format
            actions: List of action dictionaries
            days: List of days or string (e.g., 'weekdays', 'weekend', 'all')
            date: Specific date (optional)
            enabled: Whether schedule is enabled
            
        Returns:
            str: Schedule ID if successful, None otherwise
        """
        # Generate a new schedule ID
        schedule_id = str(uuid.uuid4())
        
        # Create schedule info
        schedule_info = {
            'id': schedule_id,
            'name': name,
            'time': time,
            'actions': actions,
            'enabled': enabled
        }
        
        # Add optional fields
        if days:
            schedule_info['days'] = days
        
        if date:
            schedule_info['date'] = date
        
        # Save to configuration
        if self.config_manager.add_schedule(schedule_info):
            # Add to local cache
            self.schedules[schedule_id] = schedule_info
            self.schedule_updated.emit()
            return schedule_id
        
        return None
    
    def update_schedule(self, schedule_id, **kwargs):
        """
        Update an existing schedule
        
        Args:
            schedule_id: Schedule ID
            **kwargs: Schedule fields to update
            
        Returns:
            bool: True if successful, False otherwise
        """
        if schedule_id not in self.schedules:
            logger.error(f"Cannot find schedule {schedule_id}")
            return False
        
        # Update schedule fields
        self.schedules[schedule_id].update(kwargs)
        
        # Save to configuration
        if self.config_manager.add_schedule(self.schedules[schedule_id]):
            self.schedule_updated.emit()
            return True
        
        return False
    
    def delete_schedule(self, schedule_id):
        """
        Delete a schedule
        
        Args:
            schedule_id: Schedule ID
            
        Returns:
            bool: True if successful, False otherwise
        """
        if schedule_id not in self.schedules:
            logger.error(f"Cannot find schedule {schedule_id}")
            return False
        
        # Remove from configuration
        if self.config_manager.remove_schedule(schedule_id):
            # Remove from local cache
            del self.schedules[schedule_id]
            self.schedule_updated.emit()
            return True
        
        return False
    
    def enable_schedule(self, schedule_id, enabled=True):
        """
        Enable or disable a schedule
        
        Args:
            schedule_id: Schedule ID
            enabled: True to enable, False to disable
            
        Returns:
            bool: True if successful, False otherwise
        """
        return self.update_schedule(schedule_id, enabled=enabled)
