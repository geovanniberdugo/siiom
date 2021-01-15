importScripts('https://storage.googleapis.com/workbox-cdn/releases/3.0.0/workbox-sw.js');

workbox.precaching.precacheAndRoute([
    { url: '/static/Template/jquery/vendors/bower_components/material-design-iconic-font/dist/css/material-design-iconic-font.min.css', revision: '1'},
    { url: '/static/Template/jquery/css/app.min.1.css', revision: '1' },
    { url: '/static/Template/jquery/css/app.min.2.css', revision: '1' },
    { url: '/manifest.json', revision: '1' },
    { url: '/offline', revision: '1' },
]);

const navigateRoutes = ({ url, event }) => event.request.mode === 'navigate' || event.request.headers.get('accept').includes('text/html');
const offlineHandler = ({ url, event, params}) => fetch(event.request).catch(() => caches.match('/offline'));

workbox.routing.registerRoute(navigateRoutes, offlineHandler);