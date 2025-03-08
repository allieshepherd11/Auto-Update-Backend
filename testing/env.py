import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.spatial.distance import pdist, squareform
from scipy.spatial import cKDTree

def ht(df):
    lat_min, lat_max = df['Latitude'].min(), df['Latitude'].max()
    lon_min, lon_max = df['Longitude'].min(), df['Longitude'].max()
    lat_grid, lon_grid = np.linspace(lat_min, lat_max, 200), np.linspace(lon_min, lon_max, 200)
    lat_mesh, lon_mesh = np.meshgrid(lat_grid, lon_grid)

    # Flatten the grid for efficient distance calculations
    grid_points = np.vstack([lat_mesh.ravel(), lon_mesh.ravel()]).T

    # Build a k-d tree for efficient nearest-neighbor search
    well_points = df[['Latitude', 'Longitude']].values
    tree = cKDTree(well_points)

    # Calculate the distance from each grid point to the nearest well point
    distances, _ = tree.query(grid_points, k=1)
    distance_grid = distances.reshape(lat_mesh.shape)

    # Plot the heatmap
    plt.figure(figsize=(12, 10))
    plt.contourf(lon_mesh, lat_mesh, distance_grid, levels=100, cmap='viridis')
    plt.colorbar(label='Distance to Nearest Well Point (units of degrees)')
    plt.scatter(df['Longitude'], df['Latitude'], color='red', label='Well Points')
    plt.xlabel('Longitude')
    plt.ylabel('Latitude')
    plt.title('Heatmap of Distance to Nearest Well Point')
    plt.legend()
    plt.show()


def degrees_to_feet(lat1, lon1, lat2, lon2):
    # Earth radius in feet
    earth_radius_feet = 20925524.9  # Mean Earth radius in feet
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    delta_lat = lat2 - lat1
    delta_lon = lon2 - lon1
    a = (np.sin(delta_lat / 2) ** 2 +
         np.cos(lat1) * np.cos(lat2) * np.sin(delta_lon / 2) ** 2)
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
    return earth_radius_feet * c

def heatmap(df):
    import numpy as np
    import pandas as pd
    import matplotlib.pyplot as plt
    from shapely.geometry import LineString, Point


    # Create a list of line segments using shapely
    lines = [
        LineString([(row['Longitude'], row['Latitude']),
                    (row['Longitude_BH'], row['Latitude_BH'])])
        for _, row in df.iterrows()
    ]

    # Define the grid for the heatmap
    lat_min, lat_max = df[['Latitude', 'Latitude_BH']].min().min(), df[['Latitude', 'Latitude_BH']].max().max()
    lon_min, lon_max = df[['Longitude', 'Longitude_BH']].min().min(), df[['Longitude', 'Longitude_BH']].max().max()
    lat_grid, lon_grid = np.linspace(lat_min, lat_max, 200), np.linspace(lon_min, lon_max, 200)
    lat_mesh, lon_mesh = np.meshgrid(lat_grid, lon_grid)

    # Calculate distances from each grid point to the nearest line segment
    def distance_to_nearest_line(lon, lat):
        point = Point(lon, lat)
        return min(line.distance(point) for line in lines)

    distance_grid = np.zeros_like(lat_mesh)
    for i in range(lat_mesh.shape[0]):
        for j in range(lat_mesh.shape[1]):
            distance_grid[i, j] = distance_to_nearest_line(lon_mesh[i, j], lat_mesh[i, j])

    # Plot the heatmap
    plt.figure(figsize=(12, 10))
    plt.contourf(lon_mesh, lat_mesh, distance_grid, levels=100, cmap='viridis')
    plt.colorbar(label='Distance to Nearest Line (degrees)')
    plt.scatter(df['Longitude'], df['Latitude'], color='red', label='Surface Locations')
    plt.scatter(df['Longitude_BH'], df['Latitude_BH'], color='blue', label='Bottom Hole Locations')
    plt.xlabel('Longitude')
    plt.ylabel('Latitude')
    plt.title('Heatmap of Distance to Nearest Well Line')
    plt.legend()
    plt.show()

def prodhm(df):
    import pandas as pd
    import numpy as np
    import matplotlib.pyplot as plt
    from scipy.stats import gaussian_kde

    # Extract latitude, longitude, and weights (values)
    lat = df['latitude']
    lon = df['longitude']
    values = df['value']

    # Create 2D grid for heatmap
    x_min, x_max = lon.min() - 0.01, lon.max() + 0.01
    y_min, y_max = lat.min() - 0.01, lat.max() + 0.01

    x_grid, y_grid = np.mgrid[x_min:x_max:100j, y_min:y_max:100j]
    positions = np.vstack([x_grid.ravel(), y_grid.ravel()])
    values_array = np.vstack([lon, lat])

    # Apply Gaussian KDE to smooth the values
    kde = gaussian_kde(values_array, weights=values)
    z = kde(positions).reshape(100, 100)

    # Plot the heatmap
    plt.figure(figsize=(10, 8))
    plt.imshow(
        z.T, extent=(x_min, x_max, y_min, y_max), origin='lower', cmap='hot', alpha=0.6
    )
    plt.colorbar(label='Intensity')
    plt.scatter(lon, lat, c=values, cmap='cool', edgecolor='k', s=100, label='Data Points')
    plt.xlabel('Longitude')
    plt.ylabel('Latitude')
    plt.title('Heatmap of Latitude and Longitude')
    plt.legend()
    plt.show()


def standardize(df):
    mean = np.mean(df['First12MonthOil_BBL']) 
    std = np.std(df['First12MonthOil_BBL'])    
    df['Cuml_Oil_Stnd'] = (df['First12MonthOil_BBL'] - mean) / std
    return df

df = pd.read_csv('testing/env.csv')
#df = df[['Latitude','Longitude','First12MonthOil_BBL']]
print(df.columns)
df = df.loc[df['ENVWellStatus'] == 'PRODUCING']
df = df.loc[~df['First12MonthOil_BBL'].isna()]
df = standardize(df)

print(df.columns)
exit()
heatmap(df)
