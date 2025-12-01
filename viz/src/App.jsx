import React, { useRef, useState, useEffect } from 'react';
import mapboxgl from 'mapbox-gl';
import 'mapbox-gl/dist/mapbox-gl.css';

const MAPBOX_TOKEN = import.meta.env.VITE_MAPBOX_TOKEN;
const INITIAL_CENTER = [-74.006, 40.7128];
const INITIAL_ZOOM = 10;

function App() {
  const mapContainerRef = useRef(null);
  const mapRef = useRef(null);
  const [foodGapsData, setFoodGapsData] = useState(null);
  const [hoverInfo, setHoverInfo] = useState(null);

  // Fetch data
  useEffect(() => {
    fetch('http://localhost:8000/api/food-gaps')
      .then(resp => resp.json())
      .then(json => setFoodGapsData(json))
      .catch(err => console.error('Failed to load food gaps data', err));
  }, []);

  // Initialize map
  useEffect(() => {
    if (!MAPBOX_TOKEN) return;

    mapboxgl.accessToken = MAPBOX_TOKEN;

    mapRef.current = new mapboxgl.Map({
      container: mapContainerRef.current,
      center: INITIAL_CENTER,
      zoom: INITIAL_ZOOM,
    });

    mapRef.current.addControl(new mapboxgl.NavigationControl(), 'top-right');

    mapRef.current.on('load', () => {
      // Add empty source first
      mapRef.current.addSource('foodSupplyGaps', {
        type: 'geojson',
        data: { type: 'FeatureCollection', features: [] }
      });

      // Add layers
      mapRef.current.addLayer({
        id: 'nta-fills',
        type: 'fill',
        source: 'foodSupplyGaps',
        paint: {
          'fill-color': [
            'interpolate',
            ['linear'],
            ['get', 'food_insecure_pct'],
            0.0, '#2cba00',  // Low insecurity (Good) -> Green
            0.1, '#a3ff00',
            0.15, '#fff400', // Medium -> Yellow
            0.2, '#ffa700',
            0.3, '#ff0000',  // High insecurity (Bad) -> Red
            0.4, '#8b0000'   // Very High -> Dark Red
          ],
          'fill-opacity': 0.7
        }
      });

      mapRef.current.addLayer({
        id: 'nta-borders',
        type: 'line',
        source: 'foodSupplyGaps',
        paint: {
          'line-color': '#000',
          'line-width': 0.5
        }
      });
    });

    // Hover effect
    mapRef.current.on('mousemove', 'nta-fills', (e) => {
      if (e.features.length > 0) {
        const feature = e.features[0];
        setHoverInfo({
          feature: feature,
          x: e.point.x,
          y: e.point.y
        });
        mapRef.current.getCanvas().style.cursor = 'pointer';
      }
    });

    mapRef.current.on('mouseleave', 'nta-fills', () => {
      setHoverInfo(null);
      mapRef.current.getCanvas().style.cursor = '';
    });

    return () => {
      mapRef.current.remove();
    };
  }, []);

  // Update data when available
  useEffect(() => {
    if (!foodGapsData || !mapRef.current) return;

    // Check if style is loaded before adding data
    if (mapRef.current.isStyleLoaded()) {
      const source = mapRef.current.getSource('foodSupplyGaps');
      console.log(foodGapsData)
      if (source) {
        source.setData(foodGapsData);
      }
    } else {
      mapRef.current.on('load', () => {
        const source = mapRef.current.getSource('foodSupplyGaps');
        if (source) {
          source.setData(foodGapsData);
        }
      });
    }
  }, [foodGapsData]);

  if (!MAPBOX_TOKEN) {
    return <div style={{ padding: 20 }}>Please set VITE_MAPBOX_TOKEN in your .env file</div>;
  }

  return (
    <div style={{ position: 'relative', width: '100vw', height: '100vh' }}>
      <div ref={mapContainerRef} style={{ width: '100%', height: '100%' }} />

      {hoverInfo && (
        <div className="tooltip" style={{ left: hoverInfo.x, top: hoverInfo.y }}>
          <div><strong>{hoverInfo.feature.properties.nta_name}</strong></div>
          <div>Insecurity: {(hoverInfo.feature.properties.food_insecure_pct * 100).toFixed(1)}%</div>
          <div>Gap: {Math.round(hoverInfo.feature.properties.supply_gap_lbs).toLocaleString()} lbs</div>
        </div>
      )}

      <div className="legend">
        <h3>Food Insecurity %</h3>
        <div className="legend-gradient"></div>
        <div className="legend-labels">
          <span>0%</span>
          <span>40%+</span>
        </div>
      </div>
    </div>
  );
}

export default App;
