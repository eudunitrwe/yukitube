// YukiTube writes this file into its own Firefox profile at every launch, so
// these settings always win. Everything else stays yours to change.

// Open YouTube, and skip Firefox's first-run and default-browser prompts.
user_pref("browser.startup.homepage", "https://www.youtube.com/");
user_pref("browser.startup.page", 1);
user_pref("browser.shell.checkDefaultBrowser", false);
user_pref("browser.aboutwelcome.enabled", false);
user_pref("browser.startup.homepage_override.mstone", "ignore");
user_pref("startup.homepage_welcome_url", "");
user_pref("startup.homepage_welcome_url.additional", "");
user_pref("datareporting.policy.dataSubmissionPolicyBypassNotification", true);
user_pref("browser.newtabpage.enabled", false);
user_pref("browser.tabs.warnOnClose", false);
user_pref("sidebar.revamp", false);
user_pref("browser.toolbars.bookmarks.visibility", "never");

// The bundled add-ons sit in the profile's extensions folder. Firefox only
// enables add-ons placed there without asking when this scope is allowed.
user_pref("extensions.autoDisableScopes", 0);
user_pref("extensions.enabledScopes", 15);

// One window, no tab strip: links that would open a tab or window open in
// place instead, and Alt+Left comes back.
user_pref("browser.link.open_newwindow", 1);
user_pref("browser.link.open_newwindow.restriction", 0);
user_pref("browser.link.open_newwindow.override.external", 1);
user_pref("browser.tabs.inTitlebar", 0);
user_pref("toolkit.legacyUserProfileCustomizations.stylesheets", true);

// Let YouTube start playing on its own: a video opened from the YukiTube
// remote, or the play button pressed there, never counts as a click on the
// page, so Firefox's autoplay blocking would keep it silent and paused.
user_pref("media.autoplay.default", 0);
user_pref("media.autoplay.blocking_policy", 0);

// On the first launch YukiTube starts this Firefox once, headless, with
// --marionette to put its bridge userscript into Violentmonkey; port 0 lets
// it pick a free port (written to MarionetteActivePort). Without
// --marionette this does nothing.
user_pref("marionette.port", 0);

// Dark, like the desktop.
user_pref("extensions.activeThemeID", "firefox-compact-dark@mozilla.org");
user_pref("layout.css.prefers-color-scheme.content-override", 0);
user_pref("browser.uidensity", 1);
