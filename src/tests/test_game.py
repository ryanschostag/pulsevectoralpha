'''
Test module for src/game.py
'''
import pytest
from src import game


def test_run():
	'''
	Tests the run function
	'''
	session = game.Game()
	assert session.running is True

