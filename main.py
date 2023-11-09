#!/usr/bin/env python3

import os
import sys

try:
	r2aihome = os.path.dirname(os.readlink(__file__))
	sys.path.append(r2aihome)
except:
	pass

import traceback
import r2ai
from r2ai.utils import slurp
from r2ai.models import set_default_model

have_readline = False
r2ai_history_file = "r2ai.history.txt" # windows path
if "HOME" in os.environ:
	r2ai_history_file = os.environ["HOME"] + "/.r2ai.history"
try:
    import readline
    # load readline history from ~/.r2ai.history
    readline.read_history_file(r2ai_history_file)
    have_readline = True
except:
    pass #readline not available

r2 = None
have_rlang = False
have_r2pipe = False
within_r2 = False
print = print
if os.name != "nt":
	try:
		import r2lang
		have_rlang = True
		print = r2lang.print
	except:
		try:
			import r2pipe
			have_r2pipe = True
		except:
			pass

ais = {}
ai = r2ai.Interpreter()
ais[0] = ai

def r2_cmd(x):
	global ai
	res = x
	if have_rlang:
		oc = r2lang.cmd('e scr.color')
		r2lang.cmd('e scr.color=0')
		res = r2lang.cmd(x)
		r2lang.cmd('e scr.color=' + oc)
	elif r2 is not None:
		oc = r2.cmd('e scr.color')
		r2.cmd('e scr.color=0')
		res = r2.cmd(x)
		r2.cmd('e scr.color=' + oc)
	return res

# override defaults for testing
ai.system_message = "" #
#ai.model = "llama-2-7b-chat-codeCherryPop.ggmlv3.q4_K_M.gguf"

dir_path = os.path.dirname(os.path.realpath(__file__))
model_path = dir_path + "/" + ai.model
if os.path.exists(model_path):
	ai.model = model_path

help_message = """Usage: r2ai [-option] ([query])
 r2ai !aa               run a r2 command
 r2ai -k                clear the screen
 r2ai -c [cmd] [query]  run the given r2 command with the given query
 r2ai -e [k[=v]]        set environment variable
 r2ai -f [file]         load file and paste the output
 r2ai -h | ?            show this help
 r2ai -i [file] [query] load the file contents and prompt it with the given query
 r2ai -m [file/repo]    select model from huggingface repository or local file
 r2ai -M                list supported and most common models from hf
 r2ai -n [num]          select the nth language model
 r2ai -q                quit/exit/^C
 r2ai -l                toggle the live mode
 r2ai -r [sysprompt]    define the role of the conversation
 r2ai -rf [doc/role/.f] load contents of a file to define the role
 r2ai -R                reset the chat conversation context
 r2ai -v                show r2ai version"""


def runline(usertext):
	global print
	global ai
	usertext = usertext.strip()
	if usertext == "":
		return
	if usertext.startswith("?") or usertext.startswith("-h"):
		print(help_message)
	elif usertext.startswith("clear") or usertext.startswith("-k"):
		print("\x1b[2J\x1b[0;0H\r")
	elif usertext.startswith("-M"):
		r2ai.models()
	elif usertext.startswith("-m"):
		words = usertext.split(" ")
		if len(words) > 1:
			ai.model = words[1]
			set_default_model(ai.model)
		else:
			print(ai.model)
	elif usertext == "reset" or usertext.startswith("-R"):
		ai.reset()
	elif usertext == "-q" or usertext == "exit":
		return "q"
	elif usertext.startswith("-e"):
		if len(usertext) == 2:
			print(ai.env)
		else:
			line = usertext[2:].strip().split("=")
			k = line[0]
			if len(line) > 1:
				v = line[1]
				if v == "":
					del ai.env[k]
				else:
					ai.env[k] = v
			else:
				try:
					print(ai.env[k])
				except:
					pass
	elif usertext.startswith("-s"):
		r2ai_repl()
	elif usertext.startswith("-rf"):
		if len(usertext) > 2:
			try:
				ai.system_message = slurp(usertext[3:].strip())
			except:
				print("Cannot open file")
		else:
			print(ai.system_message)
	elif usertext.startswith("-r"):
		if len(usertext) > 2:
			ai.system_message = usertext[2:].strip()
		else:
			print(ai.system_message)
	elif usertext.startswith("-m"):
		ai.live_mode = not ai.live_mode
		lms = "enabled" if ai.live_mode else "disabled"
		print("live mode is " + lms)
	elif usertext.startswith("-l"):
		ai.live_mode = not ai.live_mode
		lms = "enabled" if ai.live_mode else "disabled"
		print("live mode is " + lms)
	elif usertext.startswith("-f"):
		text = usertext[2:].strip()
		try:
			res = slurp(text)
			ai.chat(res)
		except:
			print("Cannot load file", file=sys.stderr)
	elif usertext.startswith("-i"):
		text = usertext[2:].strip()
		words = text.split(" ", 1)
		res = slurp(words[0])
		if len(words) > 1:
			que = words[1]
		else:
			que = input("[Query]> ")
		tag = "CODE" # INPUT , TEXT, ..
#r2ai.chat("Q: " + que + ":\n["+tag+"]\n"+ res+"\n[/"+tag+"]\n")
		ai.chat("Human: " + que + ":\n["+tag+"]\n"+ res+"\n[/"+tag+"]\n")
	elif usertext.startswith("-n"):
		if usertext == "-n":
			for a in ais.keys():
				model = ais[a].model
				print(f"{a}  - {model}")
		else:
			index = int(usertext[2:])
			if index not in ais:
				ais[index] = r2ai.Interpreter()
				ais[index].model = ai.model
			ai = ais[index]
	elif usertext.startswith("-v"):
		print(r2ai.VERSION)
	elif usertext.startswith("-c"):
		words = usertext[2:].strip().split(" ", 1)
		res = r2_cmd(words[0])
		if len(words) > 1:
			que = words[1]
		else:
			que = input("[Query]> ")
		tag = "CODE" # TEXT, ..
		ai.chat("Human: " + que + ":\n[" + tag + "]\n" + res + "\n[/" + tag + "]\n")
	elif usertext[0] == "!": # Deprecate. we have -c now
		if r2 is None:
			print("r2 is not available")
		elif usertext[1] == "!":
			res = r2_cmd(usertext[2:])
			que = input("[Query]> ")
			ai.chat("Q: " + que + ":\n[INPUT]\n"+ res+"\n[/INPUT]\n") # , return_messages=True)
		else:
			print(r2_cmd(usertext[1:]))
	elif usertext.startswith("-"):
		print("Unknown flag. See 'r2ai -h' for help")
	else:
		ai.chat(usertext)

def r2ai_repl():
	olivemode = ai.live_mode
	ai.live_mode = True
	oldoff = "0x00000000"
	while True:
		prompt = "[r2ai:" + oldoff + "]> "
		if r2 is not None:
			off = r2_cmd("s").strip()
			if off == "":
				off = r2_cmd("s").strip()
			if len(off) > 5:
				oldoff = off
		if ai.active_block is not None:
			#r2ai.active_block.update_from_message("")
			ai.end_active_block()
		try:
			usertext = input(prompt).strip()
		except:
			break
		try:
			if runline(usertext) == "q":
				print("leaving")
				break
		except:
			traceback.print_exc()
			continue
		readline.write_history_file(r2ai_history_file)
	ai.live_mode = olivemode

### MAIN ###
if have_r2pipe:
	try:
		if "R2PIPE_IN" in os.environ.keys():
			r2 = r2pipe.open()
			within_r2 = True
		else:
			file = sys.argv[1] if len(sys.argv) > 1 else "/bin/ls"
			r2 = r2pipe.open(file)
	except:
		traceback.print_exc()

if have_rlang:
	def r2ai_rlang_plugin(unused_but_required_argument):
		def _call(s):
			if s == "r2ai":
				print(help_message)
			elif s.startswith("r2ai"):
				usertext = s[4:].strip()
				try:
					runline(usertext)
				except Exception as e:
					print(e)
					traceback.print_exc()
				return True;
			return False

		return {
			"name": "r2ai",
			"license": "MIT",
			"desc": "run llama language models in local inside r2",
			"call": _call,
		}
	r2lang.plugin("core", r2ai_rlang_plugin)
elif len(sys.argv) > 1:
#	ai.live_mode = False
	for arg in sys.argv[1:]:
		runline(arg)
	r2ai_repl()
elif not within_r2:
	r2ai_repl()
