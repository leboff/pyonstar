# OnStar Python Troubleshooting Guide

This guide provides solutions for common issues you might encounter when using the OnStar Python library.

## Authentication Issues

### Invalid Credentials

**Problem:** Authentication fails with invalid credentials error.

**Solutions:**
- Double-check your username and password
- Ensure you're using the correct OnStar PIN
- Verify that your TOTP secret is correct
- Make sure your device_id is a valid UUID4 (generate at https://www.uuidgenerator.net/version4)
- Try logging out and back in to your OnStar account
- Check if your account is locked due to too many failed attempts

### TOTP Authentication Failures

**Problem:** Two-factor authentication fails.

**Solutions:**
- Ensure your system clock is synchronized correctly
- Verify that your TOTP secret is entered correctly
- Try regenerating your TOTP secret in your authenticator app

### Token Refresh Issues

**Problem:** Token refresh fails after previously working.

**Solutions:**
- Check your internet connection
- Delete the `gm_tokens.json` and `microsoft_tokens.json` files and try again
- Ensure your OnStar account is active and in good standing

## Connection Issues

### API Timeouts

**Problem:** Requests to the OnStar API time out.

**Solutions:**
- Check your internet connection
- Verify that the OnStar service is not experiencing an outage
- Increase the timeout values in your code
- Try using a wired connection instead of Wi-Fi

### Command Status Polling Timeouts

**Problem:** Command completes but status polling times out.

**Solutions:**
- Increase the `request_polling_timeout_seconds` parameter
- Check if your vehicle has cellular connectivity
- Verify that your vehicle has an active OnStar subscription

## Vehicle Command Issues

### Command Not Available

**Problem:** A command you want to use is not available.

**Solutions:**
- Check if the command is supported for your vehicle using `is_command_available()`
- Verify that your OnStar subscription includes the feature
- Make sure your vehicle's OnStar module is up to date
- Check if there are regional restrictions for the command

### Command Execution Fails

**Problem:** Commands are sent but fail to execute on the vehicle.

**Solutions:**
- Check if your vehicle has cellular connectivity
- Verify that there are no mechanical issues preventing the command
- Look for error messages in the command response
- Try the command again after a few minutes
- For EV charging commands, ensure your vehicle is plugged in

## Diagnostic Issues

### Missing Diagnostic Data

**Problem:** Some diagnostic data is missing from the response.

**Solutions:**
- Check if the specific diagnostic is supported by your vehicle
- Use `get_supported_diagnostics()` to see available diagnostics
- Wait a few minutes and try again
- Ensure your vehicle has recently been driven (some diagnostics require this)

### Slow Diagnostic Requests

**Problem:** Diagnostic requests take a long time to complete.

**Solutions:**
- Request only the specific diagnostics you need
- Increase the timeout values for diagnostic requests
- Set a higher value for `max_polls` when calling `diagnostics()`

## Library and Environment Issues

### Dependency Conflicts

**Problem:** Library installation fails due to dependency conflicts.

**Solutions:**
- Create a virtual environment for your project
- Update your Python version (minimum 3.8 required)
- Update pip: `pip install --upgrade pip`
- Install dependencies one by one to identify conflicts

### Debug Mode

**Problem:** Need more information to troubleshoot an issue.

**Solutions:**
- Enable debug mode by setting `debug=True` when creating the OnStar instance
- Redirect logs to a file for review
- Check for error codes and messages in the response

## Still Having Issues?

If you've tried the solutions above and are still experiencing problems:

1. Check for open issues on the GitHub repository
2. Open a new issue with detailed information about your problem
3. Include error messages, code snippets, and steps to reproduce the issue
4. Specify your vehicle make, model, and year
5. Mention your operating system and Python version 