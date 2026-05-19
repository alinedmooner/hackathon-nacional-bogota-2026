window.__env = window.__env || {};
window.__env.BACKEND_URL = "__BACKEND_URL__";
if (!window.__env.BACKEND_URL || window.__env.BACKEND_URL.startsWith("__")) {
	window.__env.BACKEND_URL = "/api";
}
