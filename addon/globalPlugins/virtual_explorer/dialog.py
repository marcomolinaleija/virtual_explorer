import ui
import wx
import addonHandler
addonHandler.initTranslation()
import os

class pathsDialog(wx.Dialog):
	"""
	Clase que lanzará el diálogo para añadir las carpetas, heredando de wx.dialog.
	"""
	def __init__(self, frame, data):
		"""
		Método de inicialización donde se creará toda la interfaz y se vincularán eventos y demás.
		"""
		#Translators: Title that will be displayed when the dialog appears.
		super(pathsDialog, self).__init__(None, -1, title=_("Explorador virtual")) #Se inicializa la clase padre para establecer el título del diálogo.

		self.data = data #Se crea una referencia local hacia el objeto de globalPlugin creado en el módulo __init__, este es pasado en uno de los parámetros en el constructor.
		self.displayed_paths = []

		#Se asigna el marco correspondiente y se crea el panel donde serán añadidos los controles de GUI.
		self.frame = frame
		self.Panel = wx.Panel(self)

		#Se crean los cuadros de texto junto con su etiqueta, para de esta forma añadirlos más adelante.
		#Translators: Label for the text area in which the absolute path will be entered using markers if these are available.
		label1 = wx.StaticText(self.Panel, wx.ID_ANY, label=_("&Ruta absoluta que desee guardar (usar marcadores si están disponibles):"))
		self.path = wx.TextCtrl(self.Panel, wx.ID_ANY)

		#Translators: Label for the text area where a common name will be written to identify the saved path.
		label2 = wx.StaticText(self.Panel, wx.ID_ANY, label=_("&Identificador de la ruta (nombre a mostrar en el menú virtual):"))
		self.identifier = wx.TextCtrl(self.Panel, wx.ID_ANY)

		# Add category selection
		label_cat = wx.StaticText(self.Panel, wx.ID_ANY, label=_("&Categoría:"))
		categories = [_("Todas")] + self.data.categories
		self.category = wx.ComboBox(self.Panel, wx.ID_ANY, choices=categories)
		self.category.Bind(wx.EVT_COMBOBOX, self.onCategoryChange)

		# Creamos el botón para permitir la selección de una ruta mediante el explorador de archivos.
		#Translators: a button to open the file explorer, allowing you to select a path more intuitively
		self.browseBTN = wx.Button(self.Panel, label=_("&Examinar..."))
		self.browseBTN.Bind(wx.EVT_BUTTON, self.onBrowse)

		label3 = wx.StaticText(self.Panel, wx.ID_ANY, label=_("&Rutas añadidas:"))
		self.list = wx.ListCtrl(self.Panel, wx.ID_ANY, style=wx.LC_LIST | wx.LC_SINGLE_SEL)
		self.list.Bind(wx.EVT_CONTEXT_MENU, self.onActions)
		self.list.Bind(wx.EVT_KEY_DOWN, self.onDeleteItem)

		#Se crean los botones junto con su respectiva vinculación a un método de evento que ejecutará ciertas acciones en base a si son pulsados.

		self.actionsBTN = wx.Button(self.Panel, label=_("Acciones"))
		self.actionsBTN.Bind(wx.EVT_BUTTON, self.onActions)
		#Translators: It is the accept button to confirm the data entered.
		self.acceptBTN = wx.Button(self.Panel, label=_("&Aceptar"))
		self.acceptBTN.Bind(wx.EVT_BUTTON, self.onAccept)
		#Translators: It is the cancel button to cancel the process and close the dialog.
		self.cancelBTN = wx.Button(self.Panel, label=_("Cancelar"))
		self.cancelBTN.Bind(wx.EVT_BUTTON, self.onCancel)
		#Translators: It is the web button to open the developer website in the browser.
		self.webBTN = wx.Button(self.Panel, label=_("&Visitar la web del desarrollador"))
		self.webBTN.Bind(wx.EVT_BUTTON, self.onWeb)
		#Se hace una vinculación hacia un método de evento para controlar teclas en la ventana.
		self.Bind(wx.EVT_CHAR_HOOK, self.onkeyWindowDialog)

		#Se crean las instancias de contenedores para añadir los controles.
		sizeV = wx.BoxSizer(wx.VERTICAL)
		sizeH = wx.BoxSizer(wx.HORIZONTAL)

		sizeV.Add(label1, 0, wx.EXPAND)
		sizeV.Add(self.path, 0, wx.EXPAND)
		sizeV.Add(label2, 0, wx.EXPAND)
		sizeV.Add(self.identifier, 0, wx.EXPAND)
		sizeV.Add(label_cat, 0, wx.EXPAND)
		sizeV.Add(self.category, 0, wx.EXPAND)
		sizeV.Add(label3, 0, wx.EXPAND)
		sizeV.Add(self.list, 1, wx.EXPAND) # Changed proportion to 1 to make it expand

		sizeH.Add(self.actionsBTN, 1, wx.EXPAND)
		sizeH.Add(self.acceptBTN, 1, wx.EXPAND)
		sizeH.Add(self.cancelBTN, 1, wx.EXPAND)
		sizeH.Add(self.webBTN, 1, wx.EXPAND)

		sizeV.Add(sizeH, 0, wx.EXPAND)

		#Se añaden estos contenedores (empaquetados en uno solo) al panel de la GUI, para luego centrar la ventana en la pantalla.
		self.Panel.SetSizer(sizeV)
		self.CenterOnScreen()

		self.category.SetValue(_("Todas"))
		self.addListItems()

	def addListItems(self, category=None):
		self.list.DeleteAllItems()
		if category and category != _("Todas"):
			self.displayed_paths = self.data.fav_paths.get(category, [])
		else:
			# Flatten the dictionary of paths into a single list and store it
			self.displayed_paths = [item for cat_paths in self.data.fav_paths.values() for item in cat_paths]
		
		# Sort the displayed list
		self.displayed_paths.sort(key=lambda x: (not x[2], x[1])) # Sort by fixed status (desc) and then by identifier (asc)

		for idx, row in enumerate(self.displayed_paths):
			# row is [path, identifier, fixed, category]
			category_str = f" ({row[3]})" if row[3] and (not category or category == _("Todas")) else ""
			fixed_str = "(Fijado) " if row[2] == 1 else ""
			self.list.InsertItem(idx, _("{fixed}Nombre: {id}, Ruta: {path}{cat}").format(
				fixed=fixed_str, id=row[1], path=row[0], cat=category_str))

	def onCategoryChange(self, event):
		selected_category = self.category.GetValue()
		self.addListItems(selected_category)

	def onActions(self, event):
		self.menu = wx.Menu()
		item1 = self.menu.Append(1, _("Fijar ruta"))
		item2 = self.menu.Append(2, _("Desfijar ruta"))
		item3 = self.menu.Append(3, _("Eliminar ruta"))
		item4 = self.menu.Append(4, _("Renombrar ruta"))
		self.menu.Bind(wx.EVT_MENU, self.onMenu)
		self.actionsBTN.PopupMenu(self.menu)

	def onDeleteItem(self, event):
		if event.GetKeyCode() == wx.WXK_DELETE:
			selected_index = self.list.GetFocusedItem()
			if selected_index == -1:
				return
			
			try:
				path_data = self.displayed_paths[selected_index]
				identifier = path_data[1]
				if self.data.deletePath(identifier):
					ui.message(_("Ruta eliminada correctamente."))
					self.addListItems() # Refresh the list
			except IndexError:
				ui.message(_("Error: la selección está fuera de rango."))
		event.Skip()

	def onMenu(self, event):
		if self.list.GetItemCount() == 0:
			ui.message(_("No hay rutas guardadas."))
			return

		id = event.GetId()
		selected_index = self.list.GetFocusedItem()
		if selected_index == -1:
			ui.message(_("Por favor, seleccione una ruta de la lista primero."))
			return

		try:
			path_data = self.displayed_paths[selected_index]
			path = path_data[0]
			identifier = path_data[1]
		except IndexError:
			ui.message(_("Error: la selección está fuera de rango."))
			return

		if id == 1: # Fix
			if self.data.fix(path, identifier):
				ui.message(_("Ruta fijada correctamente."))
				self.addListItems()

		elif id == 2: # Unfix
			if self.data.unfix(path, identifier):
				ui.message(_("Ruta desfijada correctamente."))
				self.addListItems()

		elif id == 3: # Delete
			if self.data.deletePath(identifier):
				ui.message(_("Ruta eliminada correctamente."))
				self.addListItems()

		elif id == 4: # Rename
			with wx.TextEntryDialog(self, _("Introduce el nuevo nombre para la ruta:"), _("Renombrar ruta"), identifier) as dlg:
				if dlg.ShowModal() == wx.ID_OK:
					new_identifier = dlg.GetValue()
					if self.data.renamePath(identifier, new_identifier):
						ui.message(_("Ruta renombrada correctamente."))
						self.addListItems()

	def onBrowse(self, event):
		with wx.DirDialog(self, _("Selecciona una carpeta"), style=wx.DD_DEFAULT_STYLE) as dialog:
			if dialog.ShowModal() == wx.ID_OK:
				self.path.SetValue(dialog.GetPath())
				self.identifier.SetValue(os.path.basename(dialog.GetPath()))

	def onAccept(self, event):
		if any(value == "" for value in [self.path.GetValue(), self.identifier.GetValue()]):
			ui.message(_("Asegúrese de llenar correctamente los campos solicitados."))
			self.path.SetFocus() if self.path.GetValue() == "" else self.identifier.SetFocus()
			return

		pathValue, identifierValue = self.path.GetValue(), self.identifier.GetValue()
		categoryValue = self.category.GetValue()
		pathValue = self.data.checkPath(pathValue)
		if self.data.addPath(pathValue, identifierValue, categoryValue):
			self.addListItems()
			self.path.SetValue("")
			self.identifier.SetValue("")
			self.category.SetValue("")
			self.path.SetFocus()

	def onWeb(self, event):
		wx.LaunchDefaultBrowser("https://reyesgamer.com/")

	def onkeyWindowDialog(self, event):
		if event.GetKeyCode() == 27:
			self.Close()
		else:
			event.Skip()

	def onCancel(self, event):
		self.Close()