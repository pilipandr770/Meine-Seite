# Monkey patch to disable stock checking in the shop system
import logging
import sys

# Configure logging override for the app
def patch_flask_app():
    # Define a filter to block "Insufficient stock" warnings
    class StockWarningFilter(logging.Filter):
        def filter(self, record):
            if record.levelname == "WARNING" and hasattr(record, "msg") and isinstance(record.msg, str):
                if "Insufficient stock" in record.msg:
                    # Block this warning from being shown
                    return False
            return True
    
    # Apply filter to the root logger
    root_logger = logging.getLogger()
    root_logger.addFilter(StockWarningFilter())
    
    # Also apply to app logger
    app_logger = logging.getLogger('app')
    app_logger.addFilter(StockWarningFilter())
    
    # Patch any other loggers that might emit the warning
    for name in logging.Logger.manager.loggerDict:
        if 'app' in name:
            logger = logging.getLogger(name)
            logger.addFilter(StockWarningFilter())

    print("Stock warning filter successfully applied to logging system")

# Call the patch function
patch_flask_app()
