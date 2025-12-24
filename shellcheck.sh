#!/bin/bash -e
# SPDX-FileCopyrightText: Copyright 2025 crueter
# SPDX-License-Identifier: GPL-3.0-or-later

find tools -name "*.sh" -exec shellcheck -s sh {} \;
