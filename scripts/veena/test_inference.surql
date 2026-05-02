-- 1. Switch to the correct Namespace/Database
USE NS bijmantra DB science;

-- 2. Define the Table and Fields
DEFINE TABLE crop_sensor SCHEMALESS;
DEFINE FIELD soil_moisture ON TABLE crop_sensor TYPE float;
DEFINE FIELD temperature ON TABLE crop_sensor TYPE float;
DEFINE FIELD humidity ON TABLE crop_sensor TYPE float;
DEFINE FIELD chlorophyll_index ON TABLE crop_sensor TYPE float;

-- 3. Define Fallback Inference Function (SurrealQL)
-- Heuristic: High moisture (>30) + moderate temp (<30) = Resistant (1.0)
REMOVE FUNCTION fn::drought_resistance;

DEFINE FUNCTION fn::drought_resistance($inputs: array) {
    RETURN IF ($inputs[0] > 30 AND $inputs[1] < 30) THEN
        1.0
    ELSE
        0.0
    END;
};

-- 4. Insert Test Data (One Sensitive, One Resistant)
-- Sensitive case: Low moisture, High temp
CREATE crop_sensor SET 
    soil_moisture = 13.0, 
    temperature = 33.0, 
    humidity = 22.0, 
    chlorophyll_index = 0.25;

-- Resistant case: High moisture, Moderate temp
CREATE crop_sensor SET 
    soil_moisture = 42.0, 
    temperature = 26.0, 
    humidity = 62.0, 
    chlorophyll_index = 0.85;

-- 5. Run Inference using the embedded function
-- The input tensor shape must match training: [soil_moisture, temperature, humidity, chlorophyll_index]
SELECT 
    id, 
    soil_moisture,
    fn::drought_resistance([soil_moisture, temperature, humidity, chlorophyll_index]) AS is_resistant 
FROM crop_sensor;
