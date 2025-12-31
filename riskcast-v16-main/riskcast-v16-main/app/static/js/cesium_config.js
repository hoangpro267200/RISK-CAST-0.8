/**
 * Cesium Configuration
 * Sets the base URL for Cesium workers and assets to load from local static files
 */
window.CESIUM_BASE_URL = "/static/cesium/";

if (typeof Cesium !== "undefined" && Cesium.buildModuleUrl) {
    Cesium.buildModuleUrl.setBaseUrl("/static/cesium/");
}

