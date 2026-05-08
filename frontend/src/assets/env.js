window.__env = window.__env || {};
window.__env.BACKEND_URL = "__BACKEND_URL__";
if (window.__env.BACKEND_URL === "__BACKEND_URL__") {
	// En localhost usa el proxy de Angular ('/api' → http://localhost:8000)
	// para que el AI chat funcione contra el uvicorn local.
	// En cualquier otro host, cae al staging.
	window.__env.BACKEND_URL = window.location.hostname === 'localhost'
		? "/api"
		: "https://gludsitohackathon5back.glud.org";
}
