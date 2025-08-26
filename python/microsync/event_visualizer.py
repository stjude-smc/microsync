"""
Interactive event visualization using Bokeh.

This module provides the EventVisualizer class for creating interactive
timeline visualizations of scheduled events from the sync device.
"""

import bokeh.plotting as bk
from bokeh.models import ColumnDataSource, HoverTool, BoxAnnotation
from bokeh.layouts import column
from bokeh.io import output_notebook
from collections import defaultdict
from itertools import chain
import re


class EventVisualizer:
    """Interactive Bokeh-based event visualization for sync device events."""
    
    # Configuration constants
    STATE_EVENTS = {'SET_PIN', 'TGL_PIN', 'EN__PIN', 'DIS_PIN', 'OPE_SHU', 'CLS_SHU', 'BST__ON', 'BST_OFF'}
    ACTIVE_STATES = {
        'SET_PIN': lambda e: e.arg2 == 1, 
        'TGL_PIN': lambda e: True, 
        'EN__PIN': lambda e: True,
        'DIS_PIN': lambda e: False, 
        'OPE_SHU': lambda e: True, 
        'CLS_SHU': lambda e: False,
        'BST__ON': lambda e: True, 
        'BST_OFF': lambda e: False
    }
    TYPE_PRIORITY = {'SET_PIN': 1, 'TGL_PIN': 2, 'Enabled': 3, 'Shutter': 4, 'Burst': 5}
    BOX_HEIGHT = 0.6
    INFINITE_EXTENSION = 1e9
    
    def __init__(self, shutter_delay=1000):
        """
        Initialize the event visualizer.
        
        Args:
            shutter_delay (int): Shutter delay time in microseconds
        """
        self.shutter_delay = shutter_delay
    
    def get_group_name(self, event):
        """Get the group name for an event based on its function type."""
        try:
            from .rev_pin_map import rev_pin_map
            pin_name = event.arg1 if isinstance(event.arg1, str) else rev_pin_map[event.arg1]
        except (KeyError, ImportError):
            # Fallback for unknown pin numbers
            pin_name = f"Pin{event.arg1}"
        
        if event.func in ['SET_PIN', 'TGL_PIN']:
            return f"{event.func}({pin_name})"
        elif event.func in ['EN__PIN', 'DIS_PIN']:
            return f"Enabled({pin_name})"
        elif event.func in ['OPE_SHU', 'CLS_SHU']:
            return "Shutter"
        elif event.func in ['BST__ON', 'BST_OFF']:
            return "Burst"
        return event.func
    
    def get_sort_key(self, group_name):
        """Get sorting key for group names with proper pin sorting."""
        if '(' in group_name and ')' in group_name:
            event_type, pin_name = group_name.split('(')[0], group_name.split('(')[1].rstrip(')')
            priority = self.TYPE_PRIORITY.get(event_type, 999)
            
            # Natural pin sorting
            match = re.match(r'([A-Za-z]+)(\d*)', pin_name)
            pin_key = (match.group(1), int(match.group(2) or 0)) if match else (pin_name, 0)
            return (priority, pin_key)
        else:
            return (self.TYPE_PRIORITY.get(group_name, 999), group_name)
    
    def is_active_state(self, event):
        """Determine if an event represents an active state."""
        return self.ACTIVE_STATES.get(event.func, lambda e: True)(event)
    
    def create_shutter_boxes(self, event, start_time, end_time, y_pos, color):
        """Create boxes for shutter events with transient state visualization."""
        duration = end_time - start_time
        boxes = []
        
        if duration <= self.shutter_delay:
            # Entire duration is transient
            boxes.append({
                'x': start_time,
                'y': y_pos - self.BOX_HEIGHT/2,
                'width': duration,
                'height': self.BOX_HEIGHT,
                'color': 'wheat',
                'alpha': 0.7
            })
        else:
            # Transient period + full period
            boxes.append({
                'x': start_time,
                'y': y_pos - self.BOX_HEIGHT/2,
                'width': self.shutter_delay,
                'height': self.BOX_HEIGHT,
                'color': 'wheat',
                'alpha': 0.7
            })
            boxes.append({
                'x': start_time + self.shutter_delay,
                'y': y_pos - self.BOX_HEIGHT/2,
                'width': duration - self.shutter_delay,
                'height': self.BOX_HEIGHT,
                'color': color,
                'alpha': 0.7
            })
        
        return boxes
    
    def process_state_events(self, group_events, y_pos, group_name):
        """Process state-based events and return box data."""
        # Expand and sort all repeating events
        expanded_events = list(chain.from_iterable(e.expand_repeating_events() for e in group_events))
        if not expanded_events:
            return []
        
        sorted_events = sorted(expanded_events, key=lambda e: e.ts)
        boxes = []
        current_toggle_color = 'olive'  # Start with olive
        
        for i, event in enumerate(sorted_events):
            end_time = sorted_events[i + 1].ts if i + 1 < len(sorted_events) else event.ts + self.INFINITE_EXTENSION
            
            if event.func == 'TGL_PIN':
                # Toggle events use alternating colors to indicate different states
                boxes.append({
                    'x': event.ts,
                    'y': y_pos - self.BOX_HEIGHT/2,
                    'width': end_time - event.ts,
                    'height': self.BOX_HEIGHT,
                    'color': current_toggle_color,
                    'alpha': 0.7
                })
                # Alternate between olive and teal
                current_toggle_color = 'teal' if current_toggle_color == 'olive' else 'olive'
            else:
                color = 'grey' if self.is_active_state(event) else 'white'
                if group_name == "Shutter" and event.func in ['OPE_SHU', 'CLS_SHU']:
                    boxes.extend(self.create_shutter_boxes(event, event.ts, end_time, y_pos, color))
                else:
                    boxes.append({
                        'x': event.ts,
                        'y': y_pos - self.BOX_HEIGHT/2,
                        'width': end_time - event.ts,
                        'height': self.BOX_HEIGHT,
                        'color': color,
                        'alpha': 0.7
                    })
        
        return boxes
    
    def process_non_state_events(self, group_events, y_pos):
        """Process non-state events and return box data."""
        boxes = []
        for event in group_events:
            for expanded_event in event.expand_repeating_events():
                boxes.append({
                    'x': expanded_event.ts,
                    'y': y_pos - self.BOX_HEIGHT/2,
                    'width': 50,
                    'height': self.BOX_HEIGHT,
                    'color': 'grey',
                    'alpha': 0.7
                })
        return boxes
    
    def create_plot(self, events, title=None):
        """
        Create an interactive Bokeh plot of events.
        
        Args:
            events (list): List of Event objects
            title (str, optional): Plot title
            
        Returns:
            bokeh.plotting.figure.Figure: Interactive Bokeh plot
        """
        if not events:
            print("No events to visualize")
            return None
        
        # Group events
        event_groups = defaultdict(list)
        for event in events:
            event_groups[self.get_group_name(event)].append(event)
        
        # Sort groups
        sorted_groups = sorted(event_groups.items(), key=lambda x: self.get_sort_key(x[0]))
        y_positions = {name: i for i, (name, _) in enumerate(sorted_groups)}
        
        # Create plot
        p = bk.figure(
            title=title or f'Scheduled Events ({len(events)} total)',
            x_axis_label='Time (μs)',
            y_axis_label='',
            width=800,
            height=400,
            tools='pan,box_zoom,wheel_zoom,reset,save'
        )
        
        # Process all events and collect box data
        all_boxes = []
        all_timestamps = []
        
        for group_name, group_events in sorted_groups:
            y = y_positions[group_name]
            if group_events and group_events[0].func in self.STATE_EVENTS:
                boxes = self.process_state_events(group_events, y, group_name)
            else:
                boxes = self.process_non_state_events(group_events, y)
            
            # Add group name to each box
            for box in boxes:
                box['group_name'] = group_name
            
            all_boxes.extend(boxes)
            
            # Collect timestamps for axis limits
            for event in group_events:
                for expanded_event in event.expand_repeating_events():
                    all_timestamps.append(expanded_event.ts)
        
        # Create data source for hover tooltips
        if all_boxes:
            # Extract data for ColumnDataSource
            x_centers = [box['x'] + box['width']/2 for box in all_boxes]
            y_centers = [box['y'] + box['height']/2 for box in all_boxes]
            widths = [box['width'] for box in all_boxes]
            heights = [box['height'] for box in all_boxes]
            # Create ColumnDataSource
            source = ColumnDataSource(data={
                'x': x_centers,
                'y': y_centers,
                'width': widths,
                'height': heights,
                'start_time': [box['x'] for box in all_boxes],
                'duration': [box['width'] for box in all_boxes],
                'group': [box.get('group_name', f"Row {int(box['y'] + box['height']/2)}") for box in all_boxes],
                'fill_color': [box['color'] for box in all_boxes]
            })
            
            # Draw all boxes using the data source
            p.rect(
                x='x', y='y', width='width', height='height',
                fill_color='fill_color',
                fill_alpha=0.7,
                line_color='black',
                line_width=1,
                source=source
            )
        
        # Set y-axis
        p.y_range.range_padding = 0.1
        p.yaxis.ticker = list(y_positions.values())
        p.yaxis.major_label_overrides = {v: k for k, v in y_positions.items()}
        
        # Set x-axis limits
        if all_timestamps:
            min_ts, max_ts = min(all_timestamps), max(all_timestamps)
            time_range = max_ts - min_ts if max_ts > min_ts else 1
            p.x_range.start = min_ts - time_range * 0.02
            p.x_range.end = max_ts + time_range * 0.2
        
        # Add hover tool
        hover = HoverTool(
            tooltips=[
                ("Group", "@group"),
                ("Start Time", "@start_time μs"),
                ("Duration", "@duration μs")
            ]
        )
        p.add_tools(hover)
        
        # Add grid
        p.grid.grid_line_alpha = 0.3
        
        return p
    
    def save_plot(self, plot, filename, format=None):
        """
        Save the plot to a file.
        
        Args:
            plot: Bokeh plot object
            filename (str): Output filename
            format (str, optional): Output format ('html', 'png', 'svg'). 
                                  If None, format is inferred from filename extension.
        """
        # Auto-detect format from filename if not specified
        if format is None:
            if filename.lower().endswith('.html'):
                format = 'html'
            elif filename.lower().endswith('.png'):
                format = 'png'
            elif filename.lower().endswith('.svg'):
                format = 'svg'
            else:
                format = 'html'  # Default to HTML
        
        if format == 'html':
            bk.save(plot, filename)
        elif format == 'png':
            # Use selenium for PNG export
            try:
                from bokeh.io import export_png
                from selenium import webdriver
                from webdriver_manager.chrome import ChromeDriverManager
                from selenium.webdriver.chrome.service import Service
                
                # Set up Chrome webdriver with automatic management
                service = Service(ChromeDriverManager().install())
                driver = webdriver.Chrome(service=service)
                
                # Hide toolbar for clean PNG export
                plot.toolbar_location = None
                
                export_png(plot, filename=filename, webdriver=driver)
                driver.quit()
                print(f"Successfully saved PNG to {filename}")
            except Exception as e:
                print(f"PNG export failed: {e}")
                print("Make sure Chrome browser is installed")
                print("Or use HTML format instead: plot.save_plot('events.html')")
        elif format == 'svg':
            # Use selenium for SVG export
            try:
                from bokeh.io import export_svg
                from selenium import webdriver
                from webdriver_manager.chrome import ChromeDriverManager
                from selenium.webdriver.chrome.service import Service
                
                # Set up Chrome webdriver with automatic management
                service = Service(ChromeDriverManager().install())
                driver = webdriver.Chrome(service=service)
                
                export_svg(plot, filename=filename, webdriver=driver)
                driver.quit()
                print(f"Successfully saved SVG to {filename}")
            except Exception as e:
                print(f"SVG export failed: {e}")
                print("Make sure Chrome browser is installed")
                print("Or use HTML format instead: plot.save_plot('events.html')")
        else:
            raise ValueError(f"Unsupported format: {format}")


def enable_jupyter_notebook():
    """Enable Bokeh interactive plots in Jupyter notebook."""
    output_notebook()

def display_plot(plot):
    """Display the plot in Jupyter notebook or return it for other environments."""
    try:
        # Use Bokeh's show function for proper display
        from bokeh.io import show
        show(plot)
        return plot
    except Exception:
        # Fallback to IPython display
        try:
            from IPython.display import display
            display(plot)
            return plot
        except ImportError:
            # Not in Jupyter, just return the plot
            return plot
