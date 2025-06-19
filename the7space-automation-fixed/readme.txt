=== The 7 Space Automation ===
Contributors: thehigherselfnetwork
Tags: automation, contact forms, gallery, wellness, integration
Requires at least: 5.0
Tested up to: 6.4
Requires PHP: 7.4
Stable tag: 1.0.1
License: GPLv2 or later
License URI: https://www.gnu.org/licenses/gpl-2.0.html

Integration plugin for The 7 Space Art Gallery & Wellness Center with HigherSelf Network Server automation platform.

== Description ==

The 7 Space Automation plugin seamlessly integrates your WordPress website with The 7 Space automation platform, enabling:

* **Contact Form Integration**: Automatically sync contact form submissions from Contact Form 7 and Gravity Forms
* **Gallery Management**: Sync artwork and artist information
* **Wellness Center Integration**: Manage appointments and class registrations
* **Automated Workflows**: Trigger personalized email sequences based on visitor behavior
* **Business Intelligence**: Track and analyze visitor engagement

= Features =

* Pre-configured WordPress Application Password integration
* Contact form synchronization (Contact Form 7, Gravity Forms)
* REST API endpoints for webhook integration
* Debug logging for troubleshooting
* Simple configuration interface
* Secure API communication

= Requirements =

* WordPress 5.0 or higher
* PHP 7.4 or higher
* HigherSelf Network Server (for full functionality)

== Installation ==

1. Upload the plugin files to the `/wp-content/plugins/the7space-automation` directory, or install the plugin through the WordPress plugins screen directly.
2. Activate the plugin through the 'Plugins' screen in WordPress
3. Use the Settings → The 7 Space Integration screen to configure the plugin
4. Enter your HigherSelf Network Server API details
5. Test the connection to ensure everything is working

== Configuration ==

After activation, go to **Settings → The 7 Space Integration** to configure:

1. **API URL**: Your HigherSelf Network Server URL
2. **API Key**: Generated from your HigherSelf Network Server
3. **WordPress Username**: Your WordPress admin username
4. **Application Password**: Pre-configured as `hZKd OEjZ w07V K64h CtVw MFdC`

== Frequently Asked Questions ==

= What is the WordPress Application Password? =

The WordPress Application Password is a secure way for external applications to authenticate with your WordPress site. This plugin comes pre-configured with your specific application password.

= Which contact forms are supported? =

Currently supported:
* Contact Form 7
* Gravity Forms

= How do I test if the integration is working? =

Use the "Test API Connection" button in the plugin settings to verify connectivity with your HigherSelf Network Server.

= Where can I find debug logs? =

Enable "Debug Logging" in the plugin settings. Logs will appear in your WordPress debug log and in `/wp-content/the7space-plugin.log`.

== Changelog ==

= 1.0.1 =
* Improved error handling and compatibility
* Added comprehensive debug logging
* Enhanced security checks
* Better contact form field mapping

= 1.0.0 =
* Initial release
* Contact Form 7 and Gravity Forms integration
* REST API endpoints
* Basic configuration interface

== Support ==

For support and documentation, visit:
* Plugin Documentation: https://the7space.com/automation-docs
* Support Email: tech@the7space.com
* HigherSelf Network: https://higherself.network
