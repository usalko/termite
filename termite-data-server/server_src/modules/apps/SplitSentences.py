#!/usr/bin/env .venv/bin/python3
# -*- coding: utf-8 -*-

import logging
import subprocess

class SplitSentences():

	SENTENCE_SPLITTER = 'utils/corenlp/SentenceSplitter.jar'

	def __init__( self, inputCorpusFilename, outputSentenceFilename ):
		self.logger = logging.getLogger('termite')
		command = [ "java", "-jar", "-Xmx2g", SplitSentences.SENTENCE_SPLITTER, inputCorpusFilename, outputSentenceFilename ]
		self.Shell( command )
		
	def Shell( self, command ):
		p = subprocess.Popen( command, stdout = subprocess.PIPE, stderr = subprocess.STDOUT )
		while p.poll() is None:
			line = str(p.stdout.readline(), encoding='utf-8').rstrip('\n')
			if len(line) > 0:
				self.logger.debug( line )
