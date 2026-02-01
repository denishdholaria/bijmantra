/**
 * Capacitor Configuration
 * Native mobile app settings for iOS and Android
 * 
 * To set up Capacitor:
 * 1. npm install @capacitor/core @capacitor/cli
 * 2. npx cap init
 * 3. npm install @capacitor/ios @capacitor/android
 * 4. npx cap add ios
 * 5. npx cap add android
 */

import { CapacitorConfig } from '@capacitor/cli'

const config: CapacitorConfig = {
  appId: 'com.bijmantra.app',
  appName: 'Bijmantra',
  webDir: 'dist',
  
  // Server configuration for development
  server: {
    // Use this for local development with live reload
    // url: 'http://localhost:5173',
    // cleartext: true,
    
    // Production settings
    androidScheme: 'https',
    iosScheme: 'https',
  },

  // iOS specific settings
  ios: {
    contentInset: 'automatic',
    preferredContentMode: 'mobile',
    backgroundColor: '#ffffff',
    // Enable background fetch for offline sync
    // appendUserAgent: 'Bijmantra-iOS',
  },

  // Android specific settings
  android: {
    backgroundColor: '#ffffff',
    allowMixedContent: false,
    // appendUserAgent: 'Bijmantra-Android',
  },

  // Plugins configuration
  plugins: {
    // Splash screen
    SplashScreen: {
      launchShowDuration: 2000,
      launchAutoHide: true,
      backgroundColor: '#16a34a', // Green-600
      androidSplashResourceName: 'splash',
      androidScaleType: 'CENTER_CROP',
      showSpinner: false,
      splashFullScreen: true,
      splashImmersive: true,
    },

    // Status bar
    StatusBar: {
      style: 'LIGHT',
      backgroundColor: '#16a34a',
    },

    // Keyboard
    Keyboard: {
      resize: 'body',
      resizeOnFullScreen: true,
    },

    // Push notifications
    PushNotifications: {
      presentationOptions: ['badge', 'sound', 'alert'],
    },

    // Local notifications
    LocalNotifications: {
      smallIcon: 'ic_stat_icon_config_sample',
      iconColor: '#16a34a',
    },

    // Camera for plant vision
    Camera: {
      // iOS camera permissions
    },

    // Geolocation for field locations
    Geolocation: {
      // Location permissions
    },

    // Filesystem for offline data
    Filesystem: {
      // File access permissions
    },

    // Network status
    Network: {
      // Network monitoring
    },

    // App updates
    AppUpdate: {
      // Auto-update configuration
    },

    // Barcode scanner
    BarcodeScanner: {
      // Scanner configuration
    },
  },
}

export default config
