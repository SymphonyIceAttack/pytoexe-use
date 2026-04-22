from pyproj import Transformer

# 定义转换器：WGS84 → 高斯克吕格
transformer = Transformer.from_crs("EPSG:4326", "EPSG:32650", always_xy=True)

# 转换坐标
lon, lat = 116.40, 39.90
x, y = transformer.transform(lon, lat)
print(f"平面坐标：X={x:.2f}, Y={y:.2f}")
