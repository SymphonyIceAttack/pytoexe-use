import geopandas as gpd
from shapely.geometry import Point, LineString, Polygon

# 1. 读取本地 GIS 文件（shp/geojson/gpkg）
# gdf = gpd.read_file("data.shp")  # 本地文件

# 2. 手动创建地理数据（点、线、面）
data = {
    "name": ["北京", "上海", "广州"],
    "geometry": [
        Point(116.40, 39.90),   # 点
        Point(121.47, 31.23),
        Point(113.27, 23.13)
    ]
}
gdf = gpd.GeoDataFrame(data, crs="EPSG:4326")  # WGS84 经纬度坐标系

# 3. 基础信息查看
print("数据前5行：")
print(gdf.head())
print("\n坐标系：", gdf.crs)
print("\n几何类型：", gdf.geometry.type.unique())
