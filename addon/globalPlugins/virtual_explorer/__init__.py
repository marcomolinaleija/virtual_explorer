# -*- coding: utf-8 -*-
# This file is covered by the GNU General Public License.
# See the file COPYING.txt for more details.
# Copyright (C) 2024 Ángel Reyes <angeldelosreyesfaz@gmail.com>

"""
Este addon tiene como finalidad el almacenar y administrar las rutas favoritas del usuario, para así poder lanzarlas más rápidamente.
"""

#Importamos las librerías del núcleo de NVDA
import globalPluginHandler
import ui
import gui
import globalVars
import api
import tones
import addonHandler
addonHandler.initTranslation()
from scriptHandler import script, getLastScriptRepeatCount
#Importamos librerías externas a NVDA
import os
import json
import shutil
import wx
from . import database
from .dialog import pathsDialog

def disableInSecureMode(decoratedCls):
	"""
	Decorador para deshabilitar el uso de la clase a decorar en pantallas seguras.
	"""
	if globalVars.appArgs.secure:
		return globalPluginHandler.GlobalPlugin
	return decoratedCls

@disableInSecureMode
class GlobalPlugin (globalPluginHandler.GlobalPlugin):
	"""
	Clase que hereda de globalPluginHandler.GlobalPlugin para hacer los scripts relacionados a cada combinación de teclas pulsada, así como otras operaciones lógicas para el funcionamiento del addon.
	"""
	scriptCategory = _("Virtual explorer")

	def __init__(self):
		"""
		Método de inicialización de la clase.
		"""
		super(GlobalPlugin, self).__init__()

		self.dbPath = os.path.join(globalVars.appArgs.configPath, "virtual_explorer.db")
		self.db = database.database(self.dbPath)
		self.db.migrate_schema()
		self.db.create("paths", "path text not null, identifier text not null, fixed integer not null, category text")
		
		self.fav_paths = {}
		self.categories = []
		self.category_index = -1
		self.navigation_stack = []
		self.counters = []
		self.clipboard = None
		self.clipboard_operation = None
		self.context_item_path = None

		self.markers = {
			"$users": os.path.expanduser('~'),
			"$desktop": os.path.join(os.path.expanduser('~'), "Desktop"),
			"$downloads": os.path.join(os.path.expanduser('~'), "Downloads"),
			"$documents": os.path.join(os.path.expanduser('~'), "Documents"),
			"$videos": os.path.join(os.path.expanduser('~'), "Videos"),
			"$pictures": os.path.join(os.path.expanduser('~'), "Pictures")
		}
		self._loadInfo()
		self.lastFixed = -1

	@property
	def empty(self):
		return not self.navigation_stack or not self.navigation_stack[0]

	def terminate(self):
		self.db.commit()
		self.db.close()

	def _getCurrentItem(self):
		if self.empty or self.counters[-1] < 0:
			return None, None
		current_list = self.navigation_stack[-1]
		if not current_list or self.counters[-1] >= len(current_list):
			return None, None
		item = current_list[self.counters[-1]]
		path = item[0] if isinstance(item, list) else item
		return item, path

	def fix(self, path, identifier):
		# Find the path to update its 'fixed' status in memory
		found = False
		for category, paths in self.fav_paths.items():
			for i, path_info in enumerate(paths):
				if path_info[1] == identifier:
					# Update in-memory object
					self.fav_paths[category][i][2] = 1
					found = True
					break
			if found:
				break
		
		if not found:
			ui.message(_("No fue posible fijar la ruta."))
			return False

		# Update database
		self.db.execute("update paths set fixed=? where identifier=?", (1, identifier))
		self.db.commit()

		# Reload everything to re-sort and ensure consistent state
		self._loadInfo()
		ui.message(_("Ruta fijada."))
		return True

	def unfix(self, path, identifier):
		# Find the path to update its 'fixed' status in memory
		found = False
		for category, paths in self.fav_paths.items():
			for i, path_info in enumerate(paths):
				if path_info[1] == identifier:
					# Update in-memory object
					self.fav_paths[category][i][2] = 0
					found = True
					break
			if found:
				break
		
		if not found:
			ui.message(_("No fue posible desfijar la ruta."))
			return False

		# Update database
		self.db.execute("update paths set fixed=? where identifier=?", (0, identifier))
		self.db.commit()

		# Reload everything to re-sort and ensure consistent state
		self._loadInfo()
		ui.message(_("Ruta desfijada."))
		return True

	def _loadInfo(self):
		try:
			results = self.db.execute("select * from paths")
			paths = [list(result) for result in results]
			
			# Group paths by category
			self.fav_paths = {}
			for path_info in paths:
				category = path_info[3] if path_info[3] else _("General")
				if category not in self.fav_paths:
					self.fav_paths[category] = []
				self.fav_paths[category].append(path_info)

			# Sort paths within each category
			for category, path_list in self.fav_paths.items():
				finalPaths = sorted([p for p in path_list if p[2] == 1], key=lambda x: x[1])
				otherPaths = sorted([p for p in path_list if p[2] == 0], key=lambda x: x[1])
				self.fav_paths[category] = finalPaths + otherPaths

			# Handle navigation state
			self.categories = sorted(list(self.fav_paths.keys()))
			self.category_index = -1
			
			if not self.categories:
				self.navigation_stack = [[]]
				self.counters = [-1]
			else:
				self.category_index = 0
				current_category_name = self.categories[self.category_index]
				self.navigation_stack = [self.fav_paths[current_category_name]]
				self.counters = [-1]
			
			self.lastFixed = -1 # This needs to be re-evaluated.
		except Exception as e:
			ui.message(_("Ha ocurrido un error al obtener las rutas: {}").format(e))

	def addPath(self, path, identifier, category=None, fixed=0):
		# Check if identifier exists in any category
		all_identifiers = [item[1] for cat_paths in self.fav_paths.values() for item in cat_paths]
		if identifier in all_identifiers:
			ui.message(_("Imposible añadir la ruta, el identificador ya está en uso."))
			return False

		if not os.path.exists(path):
			ui.message(_("Imposible añadir la ruta, la ruta no existe."))
			return False

		# Use default category if none provided
		if not category:
			category = _("General")

		# Add to in-memory dictionary
		if category not in self.fav_paths:
			self.fav_paths[category] = []
			self.categories = sorted(list(self.fav_paths.keys())) # Update categories list

		new_path_info = [path, identifier, fixed, category]
		self.fav_paths[category].append(new_path_info)
		# We should also sort the list here to maintain order
		# For now, let's just append. Sorting can be complex with fixed paths.

		# Add to database
		self.db.execute("insert into paths(path, identifier, fixed, category) values(?, ?, ?, ?)", (path, identifier, fixed, category))
		self.db.commit()
		
		tones.beep(432, 300)
		ui.message(_("Ruta añadida correctamente."))
		return True

	def deletePath(self, identifier):
		found_category = None
		path_index = -1

		# Find the path and its category
		for category, paths in self.fav_paths.items():
			for i, path_info in enumerate(paths):
				if path_info[1] == identifier:
					found_category = category
					path_index = i
					break
			if found_category:
				break

		if not found_category:
			return False

		# Delete from database first
		self.db.execute("delete from paths where identifier=?", (identifier,))
		self.db.commit()

		# Reload info to reflect changes and ensure consistent state
		self._loadInfo()
		
		return True

	def renamePath(self, old_identifier, new_identifier):
		# Check if new_identifier is empty or already in use
		if not new_identifier:
			ui.message(_("El nuevo identificador no puede estar vacío."))
			return False
		all_identifiers = [item[1] for cat_paths in self.fav_paths.values() for item in cat_paths]
		if new_identifier in all_identifiers:
			ui.message(_("El nuevo identificador ya está en uso."))
			return False

		found_category = None
		path_index = -1

		# Find the path and its category
		for category, paths in self.fav_paths.items():
			for i, path_info in enumerate(paths):
				if path_info[1] == old_identifier:
					found_category = category
					path_index = i
					break
			if found_category:
				break

		if not found_category:
			return False

		# Update in-memory dictionary
		self.fav_paths[found_category][path_index][1] = new_identifier

		# Update database
		self.db.execute("update paths set identifier=? where identifier=?", (new_identifier, old_identifier))
		self.db.commit()

		return True

	def renameCategory(self, old_category, new_category):
		if not new_category:
			ui.message(_("El nombre de la nueva categoría no puede estar vacío."))
			return False
		if new_category in self.categories:
			ui.message(_("La categoría ya existe."))
			return False

		# Update database
		self.db.execute("update paths set category=? where category=?", (new_category, old_category))
		self.db.commit()

		# Reload info
		self._loadInfo()
		return True

	def checkPath(self, path):
		newPath = self._checkMarkers(path)
		return newPath if newPath is not None else path

	def _checkMarkers(self, path):
		for key, value in self.markers.items():
			if path.startswith(key):
				return path.replace(key, value, 1)
		return None

	ACTION_COPY = _("Copiar")
	ACTION_CUT = _("Cortar")
	ACTION_PASTE = _("Pegar")
	ACTION_COPY_PATH = _("Copiar como ruta de acceso")

	def _is_actions_menu(self):
		if self.empty:
			return False
		current_list = self.navigation_stack[-1]
		# Check if the list matches our actions
		return current_list and current_list[0] == self.ACTION_COPY

	def _copy_item(self):
		if not self.context_item_path:
			return
		self.clipboard = self.context_item_path
		self.clipboard_operation = "copy"
		ui.message(_("Copiado, listo para pegar: {}").format(os.path.basename(self.context_item_path)))
		self.script_exitDirectory(None) # Exit actions menu

	def _cut_item(self):
		if not self.context_item_path:
			return
		self.clipboard = self.context_item_path
		self.clipboard_operation = "cut"
		ui.message(_("Cortado: {}").format(os.path.basename(self.context_item_path)))
		self.script_exitDirectory(None) # Exit actions menu

	def _paste_item(self):
		if not self.clipboard:
			ui.message(_("El portapapeles está vacío"))
			return

		# Destination is the directory of the item we opened the menu on
		dest_dir = self.context_item_path
		if not os.path.isdir(dest_dir):
			dest_dir = os.path.dirname(dest_dir)

		source_path = self.clipboard
		dest_path = os.path.join(dest_dir, os.path.basename(source_path))

		try:
			if self.clipboard_operation == "copy":
				if os.path.isdir(source_path):
					shutil.copytree(source_path, dest_path)
				else:
					shutil.copy(source_path, dest_path)
				ui.message(_("Elemento pegado."))
			elif self.clipboard_operation == "cut":
				shutil.move(source_path, dest_path)
				ui.message(_("Elemento movido."))
				self.clipboard = None
				self.clipboard_operation = None

			# Exit actions menu and refresh parent
			self.script_exitDirectory(None)
			# Refresh the view of the directory we pasted into
			new_content = [os.path.join(dest_dir, f) for f in os.listdir(dest_dir)]
			self.navigation_stack[-1] = new_content
			# Try to set focus on the new item
			try:
				self.counters[-1] = new_content.index(dest_path)
				self.script_nextPath(None) # Announce
			except (ValueError, IndexError):
				pass

		except Exception as e:
			ui.message(_("Error al pegar: {}").format(e))

	def _copy_path(self):
		if not self.context_item_path:
			return
		try:
			api.copyToClip(self.context_item_path)
			ui.message(_("Ruta copiada al portapapeles"))
		except Exception as e:
			ui.message(_("Error al copiar la ruta: {}").format(e))
		self.script_exitDirectory(None) # Exit actions menu

	@script(description=_("Muestra las acciones para el elemento actual"), gesture="kb:nvda+alt+space")
	def script_showContextMenu(self, gesture):
		item, path = self._getCurrentItem()
		if not path:
			return

		self.context_item_path = path

		actions = [self.ACTION_COPY, self.ACTION_CUT, self.ACTION_COPY_PATH]
		if self.clipboard:
			actions.append(self.ACTION_PASTE)

		self.navigation_stack.append(actions)
		self.counters.append(-1)
		self.script_nextPath(gesture)

	@script(description=_("Abre el diálogo para ingresar nuevas rutas"), gesture="kb:alt+NVDA+a")
	def script_addNewPath(self, gesture):
		dialog = pathsDialog(gui.mainFrame, self)
		gui.mainFrame.prePopup()
		dialog.Show()
		dialog.CentreOnScreen()
		gui.mainFrame.postPopup()

	@script(description=_("Entra en el directorio seleccionado o abre el archivo"), gesture="kb:alt+NVDA+l")
	def script_enterDirectory(self, gesture):
		if self._is_actions_menu():
			item, path = self._getCurrentItem()
			if item == self.ACTION_COPY:
				self._copy_item()
			elif item == self.ACTION_CUT:
				self._cut_item()
			elif item == self.ACTION_PASTE:
				self._paste_item()
			elif item == self.ACTION_COPY_PATH:
				self._copy_path()
			return

		item, path = self._getCurrentItem()
		if not path:
			return

		if os.path.isdir(path):
			try:
				content = [os.path.join(path, f) for f in os.listdir(path)]
				if not content:
					ui.message(_("Carpeta vacía"))
					return
				self.navigation_stack.append(content)
				self.counters.append(-1)
				self.script_nextPath(gesture)
			except PermissionError:
				ui.message(_("Acceso denegado"))
			except Exception as e:
				ui.message(str(e))
		else:
			try:
				os.startfile(path)
			except Exception as e:
				ui.message(str(e))

	@script(description=_("Vuelve al directorio anterior"), gesture="kb:alt+NVDA+backspace")
	def script_exitDirectory(self, gesture):
		if len(self.navigation_stack) > 1:
			self.navigation_stack.pop()
			self.counters.pop()
			item, path = self._getCurrentItem()
			identifier = os.path.basename(path) if path else _("Explorador virtual")
			ui.message(identifier)

	@script(description=_("Abre el archivo o directorio seleccionado"), gesture="kb:alt+NVDA+enter")
	def script_launchItem(self, gesture):
		if self._is_actions_menu():
			item, path = self._getCurrentItem()
			if item == self.ACTION_COPY:
				self._copy_item()
			elif item == self.ACTION_CUT:
				self._cut_item()
			elif item == self.ACTION_PASTE:
				self._paste_item()
			elif item == self.ACTION_COPY_PATH:
				self._copy_path()
			return

		item, path = self._getCurrentItem()
		if path:
			try:
				os.startfile(path)
			except Exception as e:
				ui.message(str(e))
	@script(description=_("Elimina la ruta seleccionada de favoritos"), gesture="kb:alt+NVDA+delete")
	def script_deleteItem(self, gesture):
		if self.empty or len(self.navigation_stack) > 1:
			return
		
		item, path = self._getCurrentItem()
		if item and isinstance(item, list):
			identifier = item[1]
			if self.deletePath(identifier):
				ui.message(_("Ruta {} eliminada").format(identifier))
			else:
				ui.message(_("No se pudo eliminar la ruta"))

	@script(description=_("Va al elemento anterior"), gesture="kb:alt+NVDA+j")
	def script_previousPath(self, gesture):
		if self.empty:
			ui.message(_("¡No hay rutas guardadas!"))
			return
		
		current_level_list = self.navigation_stack[-1]
		if not current_level_list:
			return

		self.counters[-1] -= 1
		if self.counters[-1] < 0:
			self.counters[-1] = len(current_level_list) - 1
		
		item, path = self._getCurrentItem()
		identifier = item[1] if isinstance(item, list) else os.path.basename(path)
		ui.message(_("{} {} de {}").format(identifier, self.counters[-1] + 1, len(current_level_list)))

	@script(description=_("Va al siguiente elemento"), gesture="kb:alt+NVDA+k")
	def script_nextPath(self, gesture):
		if self.empty:
			ui.message(_("¡No hay rutas guardadas!"))
			return

		current_level_list = self.navigation_stack[-1]
		if not current_level_list:
			return

		self.counters[-1] += 1
		if self.counters[-1] >= len(current_level_list):
			self.counters[-1] = 0
		
		item, path = self._getCurrentItem()
		identifier = item[1] if isinstance(item, list) else os.path.basename(path)
		ui.message(_("{} {} de {}").format(identifier, self.counters[-1] + 1, len(current_level_list)))

	@script(description=_("Va a la siguiente categoría"), gesture="kb:NVDA+alt+downArrow")
	def script_nextCategory(self, gesture):
		if self._is_actions_menu():
			ui.message(_("No puedes cambiar de categoría mientras estás en el menú de acciones. Pulsa alt+nvda+retroceso para salir."))
			return
		if not self.categories:
			ui.message(_("No hay categorías."))
			return

		self.category_index += 1
		if self.category_index >= len(self.categories):
			self.category_index = 0
		
		current_category_name = self.categories[self.category_index]
		num_items = len(self.fav_paths.get(current_category_name, []))
		ui.message(_("{} ({} elementos)").format(current_category_name, num_items))
		
		# Reset navigation to the new category's path list
		self.navigation_stack = [self.fav_paths[current_category_name]]
		self.counters = [-1]

	@script(description=_("Va a la categoría anterior"), gesture="kb:NVDA+alt+upArrow")
	def script_previousCategory(self, gesture):
		if self._is_actions_menu():
			ui.message(_("No puedes cambiar de categoría mientras estás en el menú de acciones. Pulsa alt+nvda+retroceso para salir."))
			return
		if not self.categories:
			ui.message(_("No hay categorías."))
			return

		self.category_index -= 1
		if self.category_index < 0:
			self.category_index = len(self.categories) - 1
		
		current_category_name = self.categories[self.category_index]
		num_items = len(self.fav_paths.get(current_category_name, []))
		ui.message(_("{} ({} elementos)").format(current_category_name, num_items))

		# Reset navigation to the new category's path list
		self.navigation_stack = [self.fav_paths[current_category_name]]
		self.counters = [-1]
