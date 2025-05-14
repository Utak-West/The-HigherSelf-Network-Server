"""
Dashboard configuration templates for The 7 Space Softr interfaces.
These configurations define visualization components that can be
implemented in Softr and connect to the Higher Self Network server.
"""
from typing import Dict, List, Optional, Any
from enum import Enum


class ChartType(str, Enum):
    """Chart types supported in Softr dashboards"""
    BAR = "bar"
    LINE = "line"
    PIE = "pie"
    AREA = "area"
    SCATTER = "scatter"
    TABLE = "table"
    METRIC = "metric"
    KANBAN = "kanban"
    CALENDAR = "calendar"
    GALLERY = "gallery"


class DashboardElement(dict):
    """Base class for dashboard visualization elements"""
    def __init__(
        self,
        element_id: str,
        title: str,
        description: Optional[str] = None,
        width: int = 12,  # Default full width in a 12-column grid
        height: int = 400,
        position: Optional[Dict[str, int]] = None,
        refresh_interval: int = 60,  # seconds
    ):
        super().__init__(
            element_id=element_id,
            title=title,
            description=description,
            width=width,
            height=height,
            position=position or {"row": 0, "col": 0},
            refresh_interval=refresh_interval
        )


class ChartElement(DashboardElement):
    """Configuration for chart visualization elements"""
    def __init__(
        self,
        element_id: str,
        title: str,
        chart_type: ChartType,
        data_source: str,  # API endpoint or collection name
        x_axis: Optional[str] = None,
        y_axis: Optional[str] = None,
        series: Optional[List[Dict[str, Any]]] = None,
        filters: Optional[Dict[str, Any]] = None,
        colors: Optional[List[str]] = None,
        show_legend: bool = True,
        **kwargs
    ):
        super().__init__(element_id, title, **kwargs)
        self.update({
            "type": "chart",
            "chart_type": chart_type,
            "data_source": data_source,
            "x_axis": x_axis,
            "y_axis": y_axis,
            "series": series or [],
            "filters": filters or {},
            "colors": colors or ["#4A6274", "#F9A26C", "#9BBEC8", "#DAAD86", "#A2836E"],
            "show_legend": show_legend
        })


class MetricElement(DashboardElement):
    """Configuration for metric/KPI visualization elements"""
    def __init__(
        self,
        element_id: str,
        title: str,
        data_source: str,
        metric_field: str,
        format: str = "number",  # number, currency, percent, etc.
        comparison_field: Optional[str] = None,
        trend_period: Optional[str] = None,
        icon: Optional[str] = None,
        **kwargs
    ):
        super().__init__(element_id, title, width=3, height=150, **kwargs)
        self.update({
            "type": "metric",
            "data_source": data_source,
            "metric_field": metric_field,
            "format": format,
            "comparison_field": comparison_field,
            "trend_period": trend_period,
            "icon": icon
        })


class TableElement(DashboardElement):
    """Configuration for table visualization elements"""
    def __init__(
        self,
        element_id: str,
        title: str,
        data_source: str,
        columns: List[Dict[str, Any]],
        pagination: bool = True,
        items_per_page: int = 10,
        sortable: bool = True,
        filterable: bool = True,
        actions: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ):
        super().__init__(element_id, title, **kwargs)
        self.update({
            "type": "table",
            "data_source": data_source,
            "columns": columns,
            "pagination": pagination,
            "items_per_page": items_per_page,
            "sortable": sortable,
            "filterable": filterable,
            "actions": actions or []
        })


class GalleryElement(DashboardElement):
    """Configuration for gallery visualization elements (for artwork)"""
    def __init__(
        self,
        element_id: str,
        title: str,
        data_source: str,
        image_field: str,
        title_field: str,
        subtitle_field: Optional[str] = None,
        description_field: Optional[str] = None,
        price_field: Optional[str] = None,
        tags_field: Optional[str] = None,
        cards_per_row: int = 3,
        **kwargs
    ):
        super().__init__(element_id, title, **kwargs)
        self.update({
            "type": "gallery",
            "data_source": data_source,
            "image_field": image_field,
            "title_field": title_field,
            "subtitle_field": subtitle_field,
            "description_field": description_field,
            "price_field": price_field,
            "tags_field": tags_field,
            "cards_per_row": cards_per_row
        })


class CalendarElement(DashboardElement):
    """Configuration for calendar visualization elements"""
    def __init__(
        self,
        element_id: str,
        title: str,
        data_source: str,
        event_title_field: str,
        start_date_field: str,
        end_date_field: str,
        location_field: Optional[str] = None,
        description_field: Optional[str] = None,
        color_field: Optional[str] = None,
        view_modes: Optional[List[str]] = None,
        default_view: str = "month",
        **kwargs
    ):
        super().__init__(element_id, title, **kwargs)
        self.update({
            "type": "calendar",
            "data_source": data_source,
            "event_title_field": event_title_field,
            "start_date_field": start_date_field,
            "end_date_field": end_date_field,
            "location_field": location_field,
            "description_field": description_field,
            "color_field": color_field,
            "view_modes": view_modes or ["month", "week", "day", "list"],
            "default_view": default_view
        })


# Dashboard Configurations

def create_sales_dashboard():
    """Create configuration for sales dashboard"""
    return {
        "dashboard_id": "the7space_sales_dashboard",
        "title": "The 7 Space Sales Dashboard",
        "description": "Overview of gallery sales performance",
        "refresh_interval": 300,  # 5 minutes
        "elements": [
            MetricElement(
                element_id="total_revenue_mtd",
                title="Revenue (MTD)",
                data_source="sales_summary",
                metric_field="revenue_mtd",
                format="currency",
                comparison_field="revenue_previous_mtd",
                trend_period="month",
                position={"row": 0, "col": 0}
            ),
            MetricElement(
                element_id="total_sales_mtd",
                title="Sales (MTD)",
                data_source="sales_summary",
                metric_field="sales_count_mtd",
                comparison_field="sales_count_previous_mtd",
                trend_period="month",
                position={"row": 0, "col": 3}
            ),
            MetricElement(
                element_id="avg_sale_price",
                title="Avg. Sale Price",
                data_source="sales_summary",
                metric_field="average_sale_price",
                format="currency",
                position={"row": 0, "col": 6}
            ),
            MetricElement(
                element_id="commission_paid",
                title="Commission Paid",
                data_source="sales_summary",
                metric_field="commission_paid_mtd",
                format="currency",
                position={"row": 0, "col": 9}
            ),
            ChartElement(
                element_id="sales_by_month",
                title="Sales Revenue by Month",
                chart_type=ChartType.BAR,
                data_source="sales_by_month",
                x_axis="month",
                y_axis="revenue",
                height=350,
                position={"row": 1, "col": 0},
                width=8
            ),
            ChartElement(
                element_id="sales_by_category",
                title="Sales by Category",
                chart_type=ChartType.PIE,
                data_source="sales_by_category",
                height=350,
                position={"row": 1, "col": 8},
                width=4
            ),
            TableElement(
                element_id="recent_sales",
                title="Recent Sales",
                data_source="recent_sales",
                columns=[
                    {"field": "date", "title": "Date", "format": "date"},
                    {"field": "artwork_title", "title": "Artwork"},
                    {"field": "artist", "title": "Artist"},
                    {"field": "price", "title": "Price", "format": "currency"},
                    {"field": "client_name", "title": "Client"},
                    {"field": "status", "title": "Status"}
                ],
                height=400,
                position={"row": 2, "col": 0}
            )
        ]
    }


def create_inventory_dashboard():
    """Create configuration for inventory dashboard"""
    return {
        "dashboard_id": "the7space_inventory_dashboard",
        "title": "The 7 Space Inventory Dashboard",
        "description": "Gallery inventory management",
        "refresh_interval": 600,  # 10 minutes
        "elements": [
            MetricElement(
                element_id="total_artworks",
                title="Total Artworks",
                data_source="inventory_summary",
                metric_field="total_artworks",
                position={"row": 0, "col": 0}
            ),
            MetricElement(
                element_id="available_artworks",
                title="Available",
                data_source="inventory_summary",
                metric_field="available_artworks",
                position={"row": 0, "col": 3}
            ),
            MetricElement(
                element_id="on_display",
                title="On Display",
                data_source="inventory_summary",
                metric_field="on_display",
                position={"row": 0, "col": 6}
            ),
            MetricElement(
                element_id="total_value",
                title="Inventory Value",
                data_source="inventory_summary",
                metric_field="total_value",
                format="currency",
                position={"row": 0, "col": 9}
            ),
            ChartElement(
                element_id="inventory_by_medium",
                title="Artwork by Medium",
                chart_type=ChartType.PIE,
                data_source="inventory_by_medium",
                height=350,
                position={"row": 1, "col": 0},
                width=4
            ),
            ChartElement(
                element_id="inventory_by_status",
                title="Artwork by Status",
                chart_type=ChartType.PIE,
                data_source="inventory_by_status",
                height=350,
                position={"row": 1, "col": 4},
                width=4
            ),
            ChartElement(
                element_id="inventory_by_price",
                title="Artwork by Price Range",
                chart_type=ChartType.BAR,
                data_source="inventory_by_price_range",
                x_axis="price_range",
                y_axis="count",
                height=350,
                position={"row": 1, "col": 8},
                width=4
            ),
            GalleryElement(
                element_id="recent_acquisitions",
                title="Recent Acquisitions",
                data_source="recent_acquisitions",
                image_field="image_url",
                title_field="title",
                subtitle_field="artist_name",
                description_field="description",
                price_field="price",
                tags_field="tags",
                height=600,
                position={"row": 2, "col": 0}
            )
        ]
    }


def create_events_dashboard():
    """Create configuration for events dashboard"""
    return {
        "dashboard_id": "the7space_events_dashboard",
        "title": "The 7 Space Events Dashboard",
        "description": "Exhibition and event management",
        "refresh_interval": 300,
        "elements": [
            MetricElement(
                element_id="upcoming_events",
                title="Upcoming Events",
                data_source="events_summary",
                metric_field="upcoming_events_count",
                position={"row": 0, "col": 0}
            ),
            MetricElement(
                element_id="this_month_events",
                title="Events This Month",
                data_source="events_summary",
                metric_field="this_month_events",
                position={"row": 0, "col": 3}
            ),
            MetricElement(
                element_id="registrations",
                title="Total Registrations",
                data_source="events_summary",
                metric_field="total_registrations",
                position={"row": 0, "col": 6}
            ),
            MetricElement(
                element_id="event_revenue",
                title="Event Revenue YTD",
                data_source="events_summary",
                metric_field="revenue_ytd",
                format="currency",
                position={"row": 0, "col": 9}
            ),
            CalendarElement(
                element_id="events_calendar",
                title="Events Calendar",
                data_source="events",
                event_title_field="title",
                start_date_field="start_datetime",
                end_date_field="end_datetime",
                location_field="location",
                description_field="description",
                color_field="event_type",
                height=600,
                position={"row": 1, "col": 0}
            ),
            ChartElement(
                element_id="events_by_type",
                title="Events by Type",
                chart_type=ChartType.BAR,
                data_source="events_by_type",
                x_axis="event_type",
                y_axis="count",
                height=350,
                position={"row": 2, "col": 0},
                width=6
            ),
            ChartElement(
                element_id="attendance_trend",
                title="Attendance Trend",
                chart_type=ChartType.LINE,
                data_source="attendance_by_month",
                x_axis="month",
                y_axis="attendance",
                height=350,
                position={"row": 2, "col": 6},
                width=6
            )
        ]
    }


def create_wellness_dashboard():
    """Create configuration for wellness services dashboard"""
    return {
        "dashboard_id": "the7space_wellness_dashboard",
        "title": "The 7 Space Wellness Dashboard",
        "description": "Wellness center service management",
        "refresh_interval": 300,
        "elements": [
            MetricElement(
                element_id="today_bookings",
                title="Today's Bookings",
                data_source="wellness_summary",
                metric_field="today_bookings",
                position={"row": 0, "col": 0}
            ),
            MetricElement(
                element_id="this_week_bookings",
                title="This Week's Bookings",
                data_source="wellness_summary",
                metric_field="this_week_bookings",
                position={"row": 0, "col": 3}
            ),
            MetricElement(
                element_id="booking_revenue",
                title="Revenue MTD",
                data_source="wellness_summary",
                metric_field="revenue_mtd",
                format="currency",
                position={"row": 0, "col": 6}
            ),
            MetricElement(
                element_id="top_service",
                title="Top Service",
                data_source="wellness_summary",
                metric_field="top_service",
                format="text",
                position={"row": 0, "col": 9}
            ),
            CalendarElement(
                element_id="booking_calendar",
                title="Booking Calendar",
                data_source="bookings",
                event_title_field="service_name",
                start_date_field="start_time",
                end_date_field="end_time",
                location_field="location",
                description_field="client_name",
                color_field="service_type",
                height=600,
                position={"row": 1, "col": 0}
            ),
            ChartElement(
                element_id="services_by_popularity",
                title="Services by Popularity",
                chart_type=ChartType.BAR,
                data_source="services_by_popularity",
                x_axis="service_name",
                y_axis="bookings_count",
                height=350,
                position={"row": 2, "col": 0},
                width=6
            ),
            ChartElement(
                element_id="bookings_by_hour",
                title="Bookings by Hour",
                chart_type=ChartType.LINE,
                data_source="bookings_by_hour",
                x_axis="hour",
                y_axis="count",
                height=350,
                position={"row": 2, "col": 6},
                width=6
            )
        ]
    }


def create_client_dashboard():
    """Create configuration for client management dashboard"""
    return {
        "dashboard_id": "the7space_client_dashboard",
        "title": "The 7 Space Client Dashboard",
        "description": "Client relationship management",
        "refresh_interval": 600,
        "elements": [
            MetricElement(
                element_id="total_clients",
                title="Total Clients",
                data_source="client_summary",
                metric_field="total_clients",
                position={"row": 0, "col": 0}
            ),
            MetricElement(
                element_id="new_clients",
                title="New Clients (30d)",
                data_source="client_summary",
                metric_field="new_clients_30d",
                position={"row": 0, "col": 3}
            ),
            MetricElement(
                element_id="repeat_clients",
                title="Repeat Clients %",
                data_source="client_summary",
                metric_field="repeat_clients_percent",
                format="percent",
                position={"row": 0, "col": 6}
            ),
            MetricElement(
                element_id="avg_client_value",
                title="Avg Client Value",
                data_source="client_summary",
                metric_field="average_client_value",
                format="currency",
                position={"row": 0, "col": 9}
            ),
            ChartElement(
                element_id="client_acquisition",
                title="Client Acquisition by Month",
                chart_type=ChartType.LINE,
                data_source="client_acquisition_by_month",
                x_axis="month",
                y_axis="new_clients",
                height=350,
                position={"row": 1, "col": 0},
                width=6
            ),
            ChartElement(
                element_id="client_interests",
                title="Client Interests",
                chart_type=ChartType.PIE,
                data_source="client_interests",
                height=350,
                position={"row": 1, "col": 6},
                width=6
            ),
            TableElement(
                element_id="top_clients",
                title="Top Clients",
                data_source="top_clients",
                columns=[
                    {"field": "name", "title": "Name"},
                    {"field": "email", "title": "Email"},
                    {"field": "total_spent", "title": "Total Spent", "format": "currency"},
                    {"field": "last_purchase", "title": "Last Purchase", "format": "date"},
                    {"field": "interests", "title": "Interests"},
                    {"field": "actions", "title": "Actions"}
                ],
                height=400,
                position={"row": 2, "col": 0}
            )
        ]
    }


# Export dashboard configurations

DASHBOARD_CONFIGS = {
    "sales": create_sales_dashboard(),
    "inventory": create_inventory_dashboard(),
    "events": create_events_dashboard(),
    "wellness": create_wellness_dashboard(),
    "clients": create_client_dashboard()
}
