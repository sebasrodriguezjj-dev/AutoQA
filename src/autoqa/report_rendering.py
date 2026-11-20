"""HTML rendering infrastructure, independent of report-data construction."""

from jinja2 import Environment, PackageLoader, select_autoescape

from autoqa.report_projection import ReportData


def render_html(payload: ReportData) -> str:
    environment = Environment(
        loader=PackageLoader("autoqa", "templates"), autoescape=select_autoescape(["html"])
    )
    return environment.get_template("report.html").render(**payload)
