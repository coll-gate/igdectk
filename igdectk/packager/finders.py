# -*- coding: utf-8; -*-
#
# Copyright (c) 2014 INRA UMR1095 GDEC

"""
Django app data finder for packagers (jquery, boostrap...)
"""

from django.contrib.staticfiles.finders import *

from igdectk.packager.templates_parser import get_installed_packages


class AppDirectoriesFinder(BaseFinder):

    """
    A static files finder that looks in the directory of each app as
    specified in the source_dir attribute.
    """
    storage_class = FileSystemStorage
    source_dir = 'static'

    def __init__(self, app_names=None, *args, **kwargs):
        # The list of apps that are handled
        self.apps = []
        # Mapping of app names to storage instances
        self.storages = OrderedDict()
        app_configs = apps.get_app_configs()
        if app_names:
            app_names = set(app_names)
            app_configs = [ac for ac in app_configs if ac.name in app_names]

        for app_config in app_configs:
            app_storage = self.storage_class(
                os.path.join(app_config.path, self.source_dir))

            if os.path.isdir(app_storage.location):
                self.storages[app_config.name] = app_storage
                if app_config.name not in self.apps:
                    self.apps.append(app_config.name)

        # get the list of installed packagers applications
        installed_apps = getattr(settings, 'INSTALLED_APPS', ())
        self.installed_packagers = []

        for app in installed_apps:
            module = __import__(app, fromlist=['*'])
            if hasattr(module, 'PACKAGER'):
                self.installed_packagers.append(getattr(module, 'PACKAGER'))

        # list of white listed packagers and versions
        self.packagers = getattr(settings, 'INSTALLED_PACKAGES', get_installed_packages())

        super(AppDirectoriesFinder, self).__init__(*args, **kwargs)

    def list(self, ignore_patterns):
        """
        List all files in all app storages.
        """
        for storage in six.itervalues(self.storages):
            if storage.exists(''):  # check if storage location exists
                for path in utils.get_files(storage, ignore_patterns):
                    print(path)
                    # for packagers we only accept specifics packages, library and versions (meaning sublib needs lib)
                    splitted_path = path.split(os.path.sep)

                    packager = self.packagers.get(splitted_path[0], None)
                    found = False

                    # others prefix that are not specified into installed_packagers are
                    # probably normal django applications
                    if splitted_path[0] in self.installed_packagers:
                        if packager:
                            for library in packager:
                                # split to have sublib when parent lib is not imported
                                if splitted_path[2] == library[0].split('.')[0]:
                                    if splitted_path[3] in library[1]:
                                        # found package.library(version)
                                        found = True
                                        break
                    else:
                        found = True

                    if not found:
                        continue

                    yield path, storage

    def find(self, path, all=False):
        """
        Looks for files in the app directories.
        """
        matches = []
        for app in self.apps:
            app_location = self.storages[app].location
            if app_location not in searched_locations:
                searched_locations.append(app_location)
            match = self.find_in_app(app, path)
            if match:
                if not all:
                    return match
                matches.append(match)
        return matches

    def find_in_app(self, app, path):
        """
        Find a requested static file in an app's static locations.
        """
        storage = self.storages.get(app)
        if storage:
            # only try to find a file if the source dir actually exists
            if storage.exists(path):
                matched_path = storage.path(path)
                if matched_path:
                    return matched_path
