"""Render an offline, captioned design overview; no game or model connections."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import json
import subprocess

ROOT = Path(__file__).resolve().parents[1] / 'build/cross-game-context-overview'
W, H = 1600, 900
BG = '#0b1220'
PANEL = '#152338'
EDGE = '#2c405c'
WHITE = '#f2f6fc'
MUTED = '#adbed5'
CYAN = '#57e0d1'
BLUE = '#81b5ff'
AMBER = '#ffd27b'
FONT_DIR = Path('/usr/share/fonts/truetype/dejavu')

def font(size, bold=False):
    return ImageFont.truetype(str(FONT_DIR / ('DejaVuSans-Bold.ttf' if bold else 'DejaVuSans.ttf')), size)

def text(draw, pos, value, size=28, fill=WHITE, bold=False):
    draw.text(pos, value, font=font(size, bold), fill=fill)

def wrap(draw, value, width, size):
    lines, line = [], ''
    for word in value.split():
        nxt = (line + ' ' + word).strip()
        if draw.textlength(nxt, font=font(size)) > width and line:
            lines.append(line)
            line = word
        else:
            line = nxt
    return lines + ([line] if line else [])

def para(draw, pos, value, width, size=28, fill=MUTED, spacing=12):
    x, y = pos
    for line in wrap(draw, value, width, size):
        text(draw, (x, y), line, size, fill)
        y += size + spacing
    return y

def panel(draw, xy, title, body='', accent=CYAN, title_size=30, body_size=25):
    x, y, x2, y2 = xy
    draw.rounded_rectangle(xy, 20, fill=PANEL, outline=EDGE, width=2)
    draw.rounded_rectangle((x, y+20, x+5, y2-20), 2, fill=accent)
    text(draw, (x+26, y+23), title, title_size, accent, True)
    if body:
        bottom = para(draw, (x+26, y+(58 if y2-y<=115 else 81)), body, x2-x-52, body_size)
        assert bottom < y2 + 5, (title, bottom, y2)

def arrow(draw, a, b, color=CYAN):
    draw.line([a,b], fill=color, width=5)
    x,y=b
    draw.polygon([(x,y),(x-13,y-8),(x-13,y+8)], fill=color)

SLIDES = [
    ('One context system. Every bot.', 'A shared conversation and status design across games.', 8,
     'One shared core. A distinct identity, viewpoint and memory for each bot.'),
    ('Status comes from the game.', 'DIT gives every consumer a consistent, versioned view.', 9,
     'Location, activity, party and progress include source, age and freshness.'),
    ('Keep the conversation together.', 'Preserve the exchange, who said each line, and what is unanswered.', 10,
     'The next bot receives the thread, so a short follow-up still makes sense.'),
    ('A complete context packet.', 'Build it for the selected speaker before each AI reply.', 10,
     'Give conversation its own space. Do not bury it behind instruction slots.'),
    ('Use the available context well.', 'Fit useful history and memory within the authorized model budget.', 9,
     'Keep the active exchange. Summarize older turns with links to their sources.'),
    ('Claims and status stay distinct.', 'Conversation can describe an action. Native state confirms it.', 9,
     'Repeating a claim never makes it true. Missing or old status stays explicit.'),
    ('Track the whole reply journey.', 'A generated line and a line the player heard are different stages.', 9,
     'Validate again before delivery. Add confirmed speech to the shared thread.'),
    ('The same core across games.', 'Game adapters supply the rules, state and visibility boundaries.', 9,
     'Personality may carry across games. Private chats and game state keep their scope.'),
    ('See what each reply knew.', 'The Admin Center inspects the same context the bot received.', 9,
     'Inspect sources, missing context and delivery so failures can be traced.'),
    ('Build small. Prove the context.', 'Start offline, then hand a focused change to you to playtest.', 8,
     'Proposed design only. No live game changes or model calls in this overview.'),
]

def render(index, title, subtitle, caption):
    im = Image.new('RGB', (W,H), BG)
    d = ImageDraw.Draw(im)
    d.rectangle((0,0,W,7), fill=CYAN)
    text(d,(70,40),'DIT / CONVERSATION + STATUS',22,CYAN,True)
    text(d,(70,94),title,51,WHITE,True)
    text(d,(70,169),subtitle,28,MUTED)
    if index == 0:
        for x,label in [(80,'FFXI'),(465,'WoW'),(850,'SWTOR'),(1235,'Other games')]:
            panel(d,(x,260,x+285,375),label,accent=BLUE)
            d.line([(x+142,375),(x+142,418)],fill=EDGE,width=4)
        d.line([(222,418),(1377,418)],fill=EDGE,width=4)
        d.line([(800,418),(800,455)],fill=CYAN,width=5)
        panel(d,(430,455,1170,655),'DIT shared context','Fresh status + shared threads + individual memories',title_size=36,body_size=29)
    elif index == 1:
        panel(d,(70,280,485,555),'Game adapters','Publish real observations, event IDs and ordered updates.',accent=BLUE)
        panel(d,(595,280,1010,555),'DIT status store','Keep actor identity, state versions and freshness.',accent=CYAN)
        panel(d,(1120,280,1535,555),'Bots + inspector','Read the same status revisions for a reply.',accent=AMBER)
        arrow(d,(500,420),(575,420)); arrow(d,(1025,420),(1100,420))
        for x,label,col in [(180,'KNOWN',CYAN),(650,'STALE',AMBER),(1120,'UNKNOWN',MUTED)]:
            text(d,(x,610),label,28,col,True)
    elif index == 2:
        panel(d,(70,250,950,350),'Player','That area was rough.',accent=BLUE,body_size=25)
        panel(d,(115,370,995,470),'Bot A','The pulls got messy near the entrance.',accent=CYAN,body_size=25)
        panel(d,(70,490,950,590),'Player','Was it the links?',accent=BLUE,body_size=25)
        panel(d,(1070,300,1530,600),'Next reply sees','The earlier topic, both speakers, the latest question, and its own real status.',accent=AMBER,body_size=26)
        text(d,(80,637),'ILLUSTRATIVE EXCHANGE',19,MUTED,True)
    elif index == 3:
        cards=[('Current status','Where I am, what I am doing.'),('Active conversation','Recent turns, speakers, reply target.'),('Thread state','Open questions and commitments.'),('Personal memory','Relevant encounters and relationships.'),('Game knowledge','Rules, era, places and objectives.'),('Voice + limits','Persona, audience and safe delivery.')]
        for j,(label,body) in enumerate(cards):
            x=70+(j%3)*510; y=260+(j//3)*215
            panel(d,(x,y,x+475,y+185),label,body,accent=CYAN if j<3 else BLUE,title_size=29,body_size=25)
    elif index == 4:
        for y,label,body,col in [
            (265,'Always retained','Current input, identity and required truth constraints',CYAN),
            (400,'Reserved space','The active conversation and unresolved follow-ups',BLUE),
            (535,'Expand when useful','Relevant memories, earlier turns and game knowledge',AMBER)]:
            panel(d,(80,y,1520,y+115),label,body,accent=col,title_size=28,body_size=25)
    elif index == 5:
        panel(d,(80,285,500,570),'What was said','“I’m crafting.”\nA conversational claim.',accent=BLUE,body_size=32)
        panel(d,(590,285,1010,570),'Observed status','Idle in town.\nLatest game observation.',accent=CYAN,body_size=32)
        panel(d,(1100,285,1520,570),'What DIT records','Activity remains idle.\nThe claim stays attributed.',accent=AMBER,body_size=31)
        text(d,(220,625),'Plans, memories and dialogue do not overwrite native outcomes.',30,MUTED)
    elif index == 6:
        labels=['Observe','Build context','AI reply','Validate','Deliver']
        for j,label in enumerate(labels):
            x=65+j*310
            panel(d,(x,295,x+270,435),label,accent=CYAN if j%2==0 else BLUE,title_size=27)
            if j<4: arrow(d,(x+276,365),(x+304,365))
        panel(d,(155,495,785,660),'Recheck before speaking','Correct actor, audience and current status.',accent=BLUE)
        panel(d,(835,495,1465,660),'Record the actual outcome','Queued, delivered, failed or unknown.',accent=AMBER)
    elif index == 7:
        panel(d,(80,275,500,655),'Per-game adapters','Native status\nGame rules and era\nDelivery and receipts',accent=BLUE,body_size=30)
        panel(d,(590,275,1010,655),'Shared DIT core','Context assembly\nThread continuity\nStatus and memory',accent=CYAN,body_size=30)
        panel(d,(1100,275,1520,655),'Each bot’s view','Own identity\nAllowed observations\nScoped memories',accent=AMBER,body_size=30)
        arrow(d,(510,465),(575,465)); arrow(d,(1020,465),(1085,465))
    elif index == 8:
        panel(d,(80,255,1520,680),'Reply inspector — design sketch',accent=CYAN,title_size=33)
        rows=[('Status','Source revision, age, known / stale / unknown'),('Conversation','Included turns, unresolved question, reply target'),('Memory','Relevant facts and their source references'),('Budget','Input size and anything omitted or summarized'),('Outcome','Model output, validation and delivery receipt')]
        for j,(label,value) in enumerate(rows):
            y=350+j*60
            text(d,(115,y),label,26,BLUE,True)
            text(d,(405,y),value,26,WHITE)
    elif index == 9:
        for x,num,label,body in [(80,'01','Context first','Preserve multi-speaker history through the real request path.'),(590,'02','Status + memory','Verify freshness, identity, privacy and corrections.'),(1100,'03','Owner playtest','Ship small when gates allow; test a natural exchange.')]:
            panel(d,(x,285,x+420,640),num+' / '+label,body,accent=CYAN if num=='01' else BLUE if num=='02' else AMBER,title_size=29,body_size=30)
    d.rounded_rectangle((65,725,1535,825),16,fill='#1c3144')
    lines=wrap(d,caption,1390,29)
    assert len(lines)<=2,caption
    for j,line in enumerate(lines): text(d,(95,743+j*38),line,29,WHITE)
    text(d,(70,850),'DESIGN PREVIEW  •  CROSS-GAME  •  CAPTIONED OVERVIEW',18,MUTED,True)
    text(d,(1390,848),f'{index+1:02d} / {len(SLIDES):02d}',20,CYAN,True)
    d.rectangle((0,H-6,int(W*(index+1)/len(SLIDES)),H),fill=CYAN)
    im.save(ROOT/f'slide-{index:02d}.png')

def main():
    ROOT.mkdir(parents=True, exist_ok=True)
    transcript=[]
    for i,(title,sub,duration,caption) in enumerate(SLIDES):
        render(i,title,sub,caption)
        transcript.extend([f'{i+1}. {title}',sub,caption,''])
    (ROOT/'Overview-transcript.txt').write_text('\n'.join(transcript)+'\n')
    (ROOT/'slides.json').write_text(json.dumps(SLIDES,indent=2)+'\n')
    thumbs=Image.new('RGB',(800,450*5),BG)
    for i in range(len(SLIDES)):
        im=Image.open(ROOT/f'slide-{i:02d}.png')
        im.thumbnail((400,225))
        thumbs.paste(im,((i%2)*400,(i//2)*225))
    thumbs.crop((0,0,800,1125)).save(ROOT/'contact-sheet.jpg')
    for i,(_,_,duration,_) in enumerate(SLIDES):
        print(f'Encoding slide {i+1}/{len(SLIDES)}',flush=True)
        subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-nostdin','-y',
            '-loop','1','-framerate','24','-i',str(ROOT/f'slide-{i:02d}.png'),
            '-t',str(duration),'-vf',f'fade=t=in:st=0:d=0.25,fade=t=out:st={duration-.25}:d=0.25,format=yuv420p',
            '-c:v','libx264','-threads','2','-preset','veryfast','-crf','20','-an',str(ROOT/f'part-{i:02d}.mp4')],check=True)
    (ROOT/'concat.txt').write_text(''.join(f"file 'part-{i:02d}.mp4'\n" for i in range(len(SLIDES))))
    subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-nostdin','-y','-f','concat','-safe','0',
        '-i',str(ROOT/'concat.txt'),'-c','copy','-movflags','+faststart',str(ROOT/'DIT-Cross-Game-Conversation-Overview.mp4')],check=True)
    print('Video complete',flush=True)

if __name__=='__main__': main()
