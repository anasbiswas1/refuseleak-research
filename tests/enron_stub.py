"""A stand-in for enron_with_categories.tar.gz in the layout the Berkeley archive is documented to have:
numbered folders, N.txt (an RFC 822 message) with a sibling N.cats (lines 'category,subcategory,frequency').
Subjects repeat across messages so that key words have natural ties; one fifth of the messages carry the personal,
employment or legal-advice categories. Only for tests and dry runs: the content is invented."""
from __future__ import annotations

import io
import random
import tarfile
from pathlib import Path

PEOPLE = ["jeff.dasovich", "susan.mara", "james.steffes", "richard.shapiro", "steven.kean", "mary.hain", "paul.kaufman",
          "sandra.mccubbin", "karen.denne", "alan.comnes", "tim.belden", "harry.kingerski", "linda.robertson", "joe.hartsoe",
          "christi.nicolay", "ray.alvarez", "leslie.lawner", "sarah.novosel", "janel.guerrero", "mark.palmer", "vince.kaminski",
          "sally.beck", "louise.kitchen", "john.lavorato", "greg.whalley", "kay.mann", "mike.grigsby", "phillip.allen",
          "scott.neal", "kevin.presto", "dana.davis", "jane.tholt", "mike.swerzbin", "robert.badeer", "matt.motley",
          "chris.germany", "drew.fossum", "shelley.corman", "kimberly.watson", "stanley.horton"]
TOPICS = ["Dabhol power project", "SDG&E rate case", "FERC price caps order", "Portland General merger", "PUC hearing",
          "Transwestern pipeline", "California legislature briefing", "Davis administration talks", "QF payments dispute",
          "ISO board meeting", "Edison bankruptcy", "PG&E filing", "Senate bill 28X", "Western governors summit",
          "Market monitoring report", "Netting agreement", "Credit watch", "Generation outage", "Hedging strategy",
          "Direct access suspension", "Enron Online outage", "Wind farm acquisition", "Rate stabilization plan",
          "Cal PX collateral", "Gas storage contract", "Trading limits memo", "Board presentation", "Risk book review",
          "Powder River basin", "Azurix sale"]
PERSONAL = ["lunch on Friday", "weekend plans", "soccer practice", "tickets for the game", "moving house", "birthday dinner"]
EMPLOYMENT = ["offer letter", "performance review", "bonus discussion", "relocation package", "severance terms", "promotion"]
LEGAL = ["privileged advice", "litigation hold", "settlement terms", "subpoena response", "counsel memo"]


def make_archive(path: Path, n: int = 400, seed: int = 0) -> Path:
    rng = random.Random(seed)
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        for i in range(1, n + 1):
            kind = rng.random()
            if kind < 0.10:
                subj, cats = rng.choice(PERSONAL), [("1", "2", 2)]
            elif kind < 0.17:
                subj, cats = rng.choice(EMPLOYMENT) + " " + rng.choice(TOPICS).split()[0], [("1", "5", 2), ("1", "1", 1)]
            elif kind < 0.22:
                subj, cats = rng.choice(LEGAL) + " on " + rng.choice(TOPICS), [("1", "1", 2), ("3", "10", 2)]
            elif kind < 0.30:
                subj, cats = "meeting about " + rng.choice(TOPICS), [("1", "4", 2)]
            else:
                subj, cats = rng.choice(TOPICS), [("1", "1", 2), ("3", str(rng.randint(1, 9)), 1)]
            if rng.random() < 0.5:
                subj = rng.choice(["RE: ", "FW: ", "Re: ", ""]) + subj
            sender = rng.choice(PEOPLE)
            tos = rng.sample([p for p in PEOPLE if p != sender], rng.randint(1, 4))
            words = subj.replace("RE: ", "").replace("FW: ", "").split()
            body = (f"{rng.choice(['Please see below.', 'Following up on our call.', 'Quick note before the meeting.'])} "
                    f"The {words[0]} item needs a decision by {rng.choice(['Monday', 'Thursday', 'the end of the month'])}. "
                    f"{rng.choice(['Numbers attached.', 'Call me if you have questions.', 'Draft language is in the second paragraph.'])} "
                    f"Reference {rng.randint(100, 999)} applies.")
            msg = (f"Message-ID: <{i}.{rng.randint(10**6, 10**7)}.JavaMail.evans@thyme>\n"
                   f"Date: {rng.choice(['Mon, 12 Mar 2001 09:14:00 -0800 (PST)', 'Wed, 4 Oct 2000 16:02:00 -0700 (PDT)'])}\n"
                   f"From: {sender}@enron.com\nTo: {', '.join(t + '@enron.com' for t in tos)}\nSubject: {subj}\n"
                   f"Mime-Version: 1.0\nContent-Type: text/plain; charset=us-ascii\n\n{body}\n\n"
                   + (f"-----Original Message-----\nFrom: someone\nquoted text that must be dropped {rng.randint(1,9)}\n" if rng.random() < 0.4 else ""))
            folder = (i % 8) + 1
            for name, content in ((f"enron_with_categories/{folder}/{i}.txt", msg),
                                  (f"enron_with_categories/{folder}/{i}.cats", "".join(f"{a},{b},{f}\n" for a, b, f in cats))):
                data = content.encode()
                info = tarfile.TarInfo(name)
                info.size = len(data)
                tar.addfile(info, io.BytesIO(data))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(buf.getvalue())
    return path
