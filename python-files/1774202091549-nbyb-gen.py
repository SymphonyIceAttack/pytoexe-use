import os
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import isodate
import time

class YouTubeVideoFinder:
    def __init__(self, api_key):
        """
        Инициализация YouTube API клиента
        API ключ можно получить в Google Cloud Console
        """
        self.youtube = build('youtube', 'v3', developerKey=api_key)
    
    def search_videos(self, query, max_results=10, duration_min=None, duration_max=None, 
                      order='relevance', published_after=None):
        """
        Поиск видео с фильтрацией по длительности
        
        Параметры:
        - query: поисковый запрос
        - max_results: максимум результатов
        - duration_min: минимальная длительность в секундах
        - duration_max: максимальная длительность в секундах
        - order: сортировка (relevance, date, rating, viewCount)
        - published_after: дата публикации (YYYY-MM-DDTHH:MM:SSZ)
        """
        try:
            # Базовый поисковый запрос
            search_request = self.youtube.search().list(
                q=query,
                part='id,snippet',
                type='video',
                maxResults=50,  # Получаем больше для фильтрации
                order=order,
                publishedAfter=published_after
            )
            
            search_response = search_request.execute()
            video_ids = [item['id']['videoId'] for item in search_response.get('items', [])]
            
            if not video_ids:
                print("Видео не найдены")
                return []
            
            # Получаем детальную информацию о видео (включая длительность)
            videos_request = self.youtube.videos().list(
                part='contentDetails,snippet,statistics',
                id=','.join(video_ids[:50])
            )
            
            videos_response = videos_request.execute()
            
            # Фильтруем по длительности
            filtered_videos = []
            for video in videos_response.get('items', []):
                # Парсим длительность из ISO 8601 формата (например, PT3M45S)
                duration_str = video['contentDetails']['duration']
                duration_seconds = self._parse_duration(duration_str)
                
                # Применяем фильтры длительности
                if duration_min and duration_seconds < duration_min:
                    continue
                if duration_max and duration_seconds > duration_max:
                    continue
                
                # Форматируем данные
                filtered_videos.append({
                    'id': video['id'],
                    'title': video['snippet']['title'],
                    'channel': video['snippet']['channelTitle'],
                    'duration_seconds': duration_seconds,
                    'duration_formatted': self._format_duration(duration_seconds),
                    'views': int(video['statistics'].get('viewCount', 0)),
                    'likes': int(video['statistics'].get('likeCount', 0)),
                    'url': f"https://youtube.com/watch?v={video['id']}",
                    'thumbnail': video['snippet']['thumbnails']['high']['url'],
                    'published_at': video['snippet']['publishedAt']
                })
                
                if len(filtered_videos) >= max_results:
                    break
            
            return filtered_videos
            
        except HttpError as e:
            print(f"Ошибка API: {e}")
            return []
    
    def _parse_duration(self, duration_iso):
        """Парсинг ISO 8601 длительности в секунды"""
        try:
            duration = isodate.parse_duration(duration_iso)
            return int(duration.total_seconds())
        except:
            return 0
    
    def _format_duration(self, seconds):
        """Форматирование секунд в ЧЧ:ММ:СС"""
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = seconds % 60
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes:02d}:{seconds:02d}"

def interactive_search():
    """Интерактивный режим поиска"""
    print("🎥 YouTube Video Finder")
    print("=" * 50)
    
    # Ввод API ключа
    api_key = input("Введите ваш YouTube API ключ: ").strip()
    if not api_key:
        print("❌ API ключ обязателен!")
        return
    
    finder = YouTubeVideoFinder(api_key)
    
    while True:
        print("\n" + "=" * 50)
        query = input("Поисковый запрос (или 'exit' для выхода): ").strip()
        
        if query.lower() == 'exit':
            break
        
        if not query:
            continue
        
        # Настройки поиска
        try:
            max_results = int(input("Максимум результатов (по умолчанию 10): ") or "10")
            min_duration = input("Минимальная длительность (секунд, Enter - пропустить): ")
            min_duration = int(min_duration) if min_duration else None
            max_duration = input("Максимальная длительность (секунд, Enter - пропустить): ")
            max_duration = int(max_duration) if max_duration else None
            
            print("\nСортировка:")
            print("1. По релевантности")
            print("2. По дате (новые)")
            print("3. По рейтингу")
            print("4. По просмотрам")
            sort_choice = input("Выберите (1-4): ")
            
            order_map = {
                '1': 'relevance',
                '2': 'date',
                '3': 'rating',
                '4': 'viewCount'
            }
            order = order_map.get(sort_choice, 'relevance')
            
            print("\n🔍 Поиск...")
            time.sleep(0.5)
            
            # Выполняем поиск
            videos = finder.search_videos(
                query=query,
                max_results=max_results,
                duration_min=min_duration,
                duration_max=max_duration,
                order=order
            )
            
            if videos:
                print(f"\n✅ Найдено {len(videos)} видео:")
                print("-" * 70)
                
                for i, video in enumerate(videos, 1):
                    print(f"\n{i}. {video['title']}")
                    print(f"   Канал: {video['channel']}")
                    print(f"   Длительность: {video['duration_formatted']}")
                    print(f"   👁 {video['views']:,} просмотров | 👍 {video['likes']:,} лайков")
                    print(f"   🔗 {video['url']}")
            else:
                print("❌ Видео не найдены под ваши критерии")
                
        except ValueError as e:
            print(f"❌ Ошибка ввода: {e}")
        except KeyboardInterrupt:
            print("\n👋 До свидания!")
            break

if __name__ == "__main__":
    interactive_search()