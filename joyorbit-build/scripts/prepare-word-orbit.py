"""Build offline word rounds from pinned SCOWL, retaining its full notice."""
from pathlib import Path
import hashlib
import itertools
import json
import re
import shutil
import subprocess
ROOT=Path(__file__).resolve().parents[1]
source=ROOT/'.sources/scowl'
revision='7e99edab8e32f9f9ea2b15f249ca8d4d67237410'
if not source.exists():
    subprocess.run(['git','clone','--depth','1','--branch','rel-2026.02.25','https://github.com/en-wl/wordlist.git',str(source)],check=True)
if subprocess.check_output(['git','-C',str(source),'rev-parse','HEAD'],text=True).strip()!=revision:
    raise SystemExit('Preserve existing source; use pinned SCOWL rel-2026.02.25.')
if subprocess.run(['git','-C',str(source),'diff','--quiet']).returncode:
    raise SystemExit('Preserve modified SCOWL source before generation.')
if not (source/'scowl.db').exists():
    subprocess.run(['python3','combine.py','create-db','scowl.db'],cwd=source,check=True)
command=['python3','scowl','--db','scowl.db','word-list','35','A','1','--categories=','--wo-poses=abbr','--wo-usage-notes=offensive-1,offensive-2,vulgar-1,vulgar-2']
result=subprocess.run(command,cwd=source,capture_output=True,text=True,check=True)
# Names, punctuation, abbreviations and accents are not admitted. Additional
# entries are excluded independently of SCOWL's incomplete usage labels; this
# filter is not a claim of completed editorial review of the upstream corpus.
excluded={'sex','sexes','sexy','sexual','sexuals','arse','arses','ass','asses','piss','pissed','pisses','pissing','tit','tits','porn','porno','pornographic'}
words=sorted({w for w in result.stdout.splitlines() if re.fullmatch('[a-z]{3,8}',w) and w not in excluded})
by_letters={}
for word in words:by_letters.setdefault(frozenset(word),[]).append(word)
rounds=[]
# Every answer comes from the licensed dictionary, and every round includes
# an answer using all seven letters plus at least eleven other answers.
for letters in sorted({''.join(sorted(s)) for s in by_letters if len(s)==7},key=lambda value:hashlib.sha256(value.encode()).digest()):
    possible=[]
    for n in range(1,8):
        for subset in itertools.combinations(letters,n):possible.extend(by_letters.get(frozenset(subset),[]))
    for center in letters:
        answers=sorted(w for w in possible if center in w)
        if 12 <= len(answers) <= 36:
            rounds.append({'letters':letters,'center':center,'answers':answers})
            break
    if len(rounds)==120:break
if len(rounds)!=120:raise SystemExit('Insufficient verified playable word rounds; inspect pinned source.')
data=ROOT/'games/data';data.mkdir(parents=True,exist_ok=True)
(data/'word-orbit.json').write_text(json.dumps({'version':1,'source_revision':revision,'scowl_size':35,'dialect':'American English','rounds':rounds},separators=(',',':'))+'\n')
shutil.copy2(source/'Copyright',ROOT/'theme/licenses/SCOWL-Copyright.txt')
print('Generated',len(rounds),'offline rounds from',len(words),'filtered source words.')
