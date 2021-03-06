# -*- Mode: python; tab-width: 4; indent-tabs-mode: nil; c-basic-offset: 4 -*- */
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#

from __future__ import unicode_literals

from django.db import models

class MissingSymbolConfig(models.Model):

    last_time = models.DateTimeField()

class MissingSymbol(models.Model):

    symbol_file = models.CharField(max_length=255, db_index=True)
    debug_id = models.CharField(max_length=100, db_index=True)
    code_id = models.CharField(max_length=100, db_index=True)
    code_name = models.CharField(max_length=255, db_index=True)

class SymbolsUpload(models.Model):

    upload_time = models.DateTimeField()

    comment = models.TextField(
            help_text='A comment explaining where these symbols are comming from')

    files = models.TextField(
            help_text='A list with all the files contained in that upload')

    system_symbols = models.BooleanField(
            help_text='This contains system symbols and not LibreOffice symbols',
            default=False)

# vim:set shiftwidth=4 softtabstop=4 expandtab: */
