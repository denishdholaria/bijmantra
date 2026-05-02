import ee from '@google/earthengine';

/**
 * Service to handle Google Earth Engine (GEE) interactions.
 * Note: GEE requires authentication via an OAuth2 token or a backend proxy.
 */
export class EarthEngineService {
  private static instance: EarthEngineService;
  private isInitialized = false;

  private constructor() {}

  public static getInstance(): EarthEngineService {
    if (!EarthEngineService.instance) {
      EarthEngineService.instance = new EarthEngineService();
    }
    return EarthEngineService.instance;
  }

  /**
   * Initialize the Earth Engine client library.
   * @param token OAuth2 access token for the user or service account.
   */
  public async initialize(token: string): Promise<void> {
    if (this.isInitialized) return;

    if (!token) {
      console.error('GEE Authentication Error: No OAuth2 token provided.');
      console.info('👉 Please refer to docs/manuals/GEE_AUTH_GUIDE.md for setup instructions.');
      throw new Error('Earth Engine Authentication Failed: Missing Token');
    }

    return new Promise((resolve, reject) => {
      ee.data.setAuthToken(
        '', 
        'Bearer', 
        token, 
        3600, // Expiry
        [], 
        undefined, 
        false
      );

      ee.initialize(
        null, 
        null, 
        () => {
          this.isInitialized = true;
          resolve();
        }, 
        (error: any) => reject(error)
      );
    });
  }

  /**
   * Get a MapID (tile URL template) for a Sentinel-2 image collection (NDVI).
   * @param region Geometry (GeoJSON) or Bounds to filter.
   * @param startDate Start date (YYYY-MM-DD).
   * @param endDate End date (YYYY-MM-DD).
   */
  public getSentinelNDVI(region: any, startDate: string, endDate: string): Promise<any> {
    return new Promise((resolve, reject) => {
      // Define Sentinel-2 Image Collection
      const s2 = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
        .filterDate(startDate, endDate)
        .filterBounds(region)
        .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20));

      // Compute NDVI
      const addNDVI = (image: any) => {
        const ndvi = image.normalizedDifference(['B8', 'B4']).rename('NDVI');
        return image.addBands(ndvi);
      };

      const withNDVI = s2.map(addNDVI);
      
      // Select NDVI band and mosaic (greenest pixel)
      const greenest = withNDVI.qualityMosaic('NDVI').select('NDVI');

      // Visualization parameters
      const visParams = {
        min: 0,
        max: 0.8,
        palette: ['FFFFFF', 'CE7E45', 'DF923D', 'F1B555', 'FCD163', '99B718', '74A901', '66A000', '529400', '3E8601', '207401', '056201', '004C00', '023B01', '012E01', '011D01', '011301'],
      };

      greenest.getMap(visParams, (mapId: any) => {
        if (mapId) {
          resolve(mapId); // Contains mapid and token for tile URL
        } else {
          reject(new Error('Failed to get MapID'));
        }
      });
    });
  }
}

export const earthEngineService = EarthEngineService.getInstance();
