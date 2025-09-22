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
	scriptCategory = _("Rutas fav")

	def __init__(self):
		"""
		Método de inicialización de la clase.
		"""
		super(GlobalPlugin, self).__init__()

		self.dbPath = os.path.join(globalVars.appArgs.configPath, "rutas_fav.db")
		self.db = database.database(self.dbPath)
		self.db.create("paths", "path text not null, identifier text not null, fixed integer not null")
		
		self.fav_paths = []
		self.navigation_stack = []
		self.counters = []

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
		try:
			idx = self.fav_paths.index([path, identifier, 0])
			self.fav_paths[idx][2] = 1
			new = self.fav_paths.pop(idx)
			self.fav_paths.insert((self.lastFixed+1), new)
			self.lastFixed = self.fav_paths.index(new)
			self.db.execute("update paths set fixed=? where identifier=?", (1, identifier))
			self.db.commit()
			return True
		except ValueError:
			ui.message(_("No fue posible fijar la ruta."))
			return False

	def unfix(self, path, identifier):
		try:
			idx = self.fav_paths.index([path, identifier, 1])
			self.fav_paths[idx][2] = 0
			new = self.fav_paths.pop(idx)
			self.fav_paths.append(new)
			self.db.execute("update paths set fixed=? where identifier=?", (0, identifier))
			self.db.commit()
			return True
		except ValueError:
			ui.message(_("No fue posible desfijar la ruta."))
			return False

	def convertFormat(self):
		filename = os.path.join(globalVars.appArgs.configPath, "rutas_fav.json")
		if os.path.exists(filename):
			try:
				with open(filename, "r") as f:
					paths = json.load(f)
					for path, identifier in zip(paths.get('path', []), paths.get('identifier', [])):
						self.db.execute("insert into paths(path, identifier, fixed) values(?, ?, ?)", (path, identifier, 0))
					self.db.commit()
				os.remove(filename)
			except (FileNotFoundError, json.JSONDecodeError):
				ui.message(_("error en la decodificación de json."))

	def _loadInfo(self):
		self.convertFormat()
		try:
			results = self.db.execute("select * from paths")
			paths = [list(result) for result in results]
			finalPaths = sorted([p for p in paths if p[2] == 1], key=lambda x: x[1])
			self.lastFixed = len(finalPaths) - 1
			otherPaths = sorted([p for p in paths if p[2] == 0], key=lambda x: x[1])
			self.fav_paths = finalPaths + otherPaths
			
			self.navigation_stack = [self.fav_paths]
			self.counters = [-1]
		except Exception as e:
			ui.message(_("Ha ocurrido un error al obtener las rutas: {}").format(e))

	def addPath(self, path, identifier, fixed=0):
		identifiers = [value[1] for value in self.fav_paths]
		if os.path.exists(path) and identifier not in identifiers:
			self.fav_paths.append([path, identifier, fixed])
			self.db.execute("insert into paths(path, identifier, fixed) values(?, ?, ?)", (path, identifier, fixed))
			self.db.commit()
			tones.beep(432, 300)
			ui.message(_("Ruta añadida correctamente."))
			return True
		else:
			ui.message(_("Imposible añadir la ruta a la lista, favor de escribir correctamente la misma o verificar si su identificador no es igual al de uno ya existente."))
			return False

	def deletePath(self, identifier):
		try:
			idx = [item[1] for item in self.fav_paths].index(identifier)
			self.fav_paths.pop(idx)
			self.db.execute("delete from paths where identifier=?", (identifier,))
			self.db.commit()
			if self.counters[0] >= len(self.fav_paths):
				self.counters[0] = len(self.fav_paths) - 1
			return True
		except ValueError:
			return False

	def renamePath(self, old_identifier, new_identifier):
		if not new_identifier or new_identifier in [item[1] for item in self.fav_paths]:
			ui.message(_("El nuevo identificador no puede estar vacío o ya está en uso."))
			return False
		try:
			idx = [item[1] for item in self.fav_paths].index(old_identifier)
			self.fav_paths[idx][1] = new_identifier
			self.db.execute("update paths set identifier=? where identifier=?", (new_identifier, old_identifier))
			self.db.commit()
			return True
		except ValueError:
			return False

	def checkPath(self, path):
		newPath = self._checkMarkers(path)
		return newPath if newPath is not None else path

	def _checkMarkers(self, path):
		for key, value in self.markers.items():
			if path.startswith(key):
				return path.replace(key, value, 1)
		return None

	@script(description=_("Abre el diálogo para ingresar nuevas rutas"), gesture="kb:alt+NVDA+a")
	def script_addNewPath(self, gesture):
		dialog = pathsDialog(gui.mainFrame, self)
		gui.mainFrame.prePopup()
		dialog.Show()
		dialog.CentreOnScreen()
		gui.mainFrame.postPopup()

	@script(description=_("Entra en el directorio seleccionado o abre el archivo"), gesture="kb:alt+NVDA+l")
	def script_enterDirectory(self, gesture):
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
			identifier = os.path.basename(path) if path else _("Rutas favoritas")
			ui.message(identifier)

	@script(description=_("Abre el archivo o directorio seleccionado"), gesture="kb:alt+NVDA+enter")
	def script_launchItem(self, gesture):
		item, path = self._getCurrentItem()
		if path:
			try:
				os.startfile(path)
			except Exception as e:
				ui.message(str(e))

	@script(description=_("Elimina la ruta seleccionada de favoritos"), gesture="kb:delete")
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
