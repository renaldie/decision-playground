"""
Decision Playground Entrypoint
"""
import logging
import flask.cli

# Suppress Flask development server startup banner and warnings
flask.cli.show_server_banner = lambda *args, **kwargs: None

# Suppress Werkzeug HTTP request access logs (e.g. GET /_dash-dependencies, GET /assets/...)
werkzeug_log = logging.getLogger("werkzeug")
werkzeug_log.setLevel(logging.ERROR)
werkzeug_log.disabled = True

from app import app

# Suppress internal Flask / Dash logger output
app.logger.setLevel(logging.ERROR)
app.server.logger.setLevel(logging.ERROR)


def main():
    print("=" * 60)
    print("Starting Decision Playground...")
    print("Serving on: http://127.0.0.1:8050")
    print("=" * 60)
    app.run(
        host="127.0.0.1",
        port=8050,
        debug=False,
        dev_tools_silence_routes_logging=True,
    )


if __name__ == "__main__":
    main()
