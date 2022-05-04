#!/usr/bin/env .venv/bin/python3
# -*- coding: utf-8 -*-

from handlers.Home_Core import Home_Core

def index():
	handler = Home_Core(request, response)
	return handler.GenerateResponse()
