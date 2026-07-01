import discord
from discord.ext import commands
import asyncio
import random
import json
import os
from collections import deque

# ─── KONFIGURACJA ────────────────────────────────────────────────────────────────
import os

TOKEN = os.getenv("DISCORD_TOKEN")
bot.run(TOKEN)
GUILD_ID   = 1279536565537738865
PREFIX     = "-"
OWNER_ID   = 1195685896050180146
LOG_CHANNEL_ID = 1520162367076438016
DATA_FILE  = 'data.json'

PING_DELAY   = 0.5
DELETE_DELAY = 0.5
SPAM_DELAY   = 0.4
DM_DELAY     = 1.0
CYTAT_HISTORIA_MAX = 10

# Lista przechowująca wszystkie aktywne zadania (do poprawnego działania -stop)
all_active_tasks = []

# ─── ZARZĄDZANIE DANYMI ──────────────────────────────────────────────────────────
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return {
                "admins": set(data.get("admins", [OWNER_ID])),
                "mods": set(data.get("mods", [])),
                "whitelist": set(data.get("whitelist", [])),
                "targets": set(data.get("targets", [])),
                "djs": set(data.get("djs", []))
            }
    return {"admins": {OWNER_ID}, "mods": set(), "whitelist": set(), "targets": set(), "djs": set()}

def save_data():
    data_to_save = {
        "admins": list(storage["admins"]),
        "mods": list(storage["mods"]),
        "whitelist": list(storage["whitelist"]),
        "targets": list(storage["targets"]),
        "djs": list(storage["djs"])
    }
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data_to_save, f, indent=4)

storage = load_data()

def is_admin(user_id):
    return user_id in storage["admins"] or user_id == OWNER_ID

def is_mod(user_id):
    return user_id in storage["mods"] or is_admin(user_id)

# POPRAWKA #3: Dodano brakującą funkcję is_protected()
def is_protected(user_id):
    return (
        user_id == OWNER_ID
        or user_id in storage["admins"]
        or user_id in storage["mods"]
        or user_id in storage["whitelist"]
    )

def can_attack(attacker_id, target_id):
    if attacker_id == OWNER_ID: return True
    if is_admin(attacker_id):
        if target_id == OWNER_ID or target_id in storage["admins"]: return False
        return True
    if is_mod(attacker_id):
        if target_id == OWNER_ID or target_id in storage["admins"] or target_id in storage["mods"] or target_id in storage["whitelist"]:
            return False
        return True
    return False

# ─── BAZA CYTATÓW ────────────────────────────────────────────────────────────────
CYTATY = [
    ("Kto sie nie tieruje, ten do nieba nie poleci.", "Mistrz Patryk dopelnienie", "sword"),
    ("Patrykowi snilo sie, ze jest tierem. Skad wiem, ze tier nie sni teraz, ze jest Patrykiem?", "Paradoks Patryka", "sword"),
    ("Tier to nie stan ducha. Tier to stan bycia Patrykiem na poziomie transcendentnym.", "Patryk, po trzecim tierowaniu", "sword"),
    ("Nie pytaj co tier moze zrobic dla ciebie. Zapytaj, czy jestes wystarczajaco Patrykiem.", "Patryk o zyciu", "sword"),
    ("HT1 to nie tier. To wyrok. Marlowww go wydal, Patryk go wykona.", "Komentator Crystal PvP", "crystal"),
    ("Marlowww jest numerem jeden - na razie. W srodku boi sie, bo wie, ze Patryk sie rozgrzewa.", "Ekspert Crystal PvP", "crystal"),
    ("vZylakk ma LT4 na Nethop, HT4 na PotPvP i LT4 na Crystal PvP. Jedni zbieraja trofea, on zbiera serwery.", "Kronikarz Tierow", "shield"),
    ("vZylakk nie gra na trzech serwerach naraz i na kazdym jest za dobry dla wiekszosci.", "Admin Panelu", "shield"),
    ("Heroine_BOSS ma LT4 na PotPvP i dziewiczego wasa. Dwie legendy w jednej osobie.", "Sprawozdawca Tierow", "crown"),
    ("Miec Solll w znajomych to nie przywilej. To dowod, ze Bog Tierow cie zauwazyl.", "Wyznanie Gracza", "god"),
    ("Solll nie gra na serwerze. Solll pozwala serwerowi istniec w swojej obecnosci.", "Kronika Bogow", "god"),
    ("GetherTV to najlepszy developer na swiecie. Reszta developerow to tylko tlo dla jego commitow.", "Senior Reviewer", "computer"),
    ("tturbozaspa robi edity tak dobre, ze ogladasz je dwa razy - raz z wrazenia, raz bo nie mozesz uwierzyc.", "Krytyk Montazu", "camera"),
    ("Klan ITAG nie gra w nozki. Klan ITAG definiuje czym nozki sa.", "Historyk potworowo.pl", "flag"),
    ("xxksawi rzadzi serwerem. ciapataanie rzadzi xxksawi. Tak dziala natura.", "Obserwator Nozek", "boot"),
    ("Pawciolek nie rajduje baz. On po prostu puka do drzwi, a bazy same sie rozpadaja.", "Legenda Rust", "fire"),
    ("Mowia, ze Rust jest trudny. Pawciolek mowi, ze to symulator zbierania surowcow od innych.", "Ekspert Survivalu", "fire"),
    ("Gdy Pawciolek wchodzi na serwer Rust, inne klany automatycznie oddaja mu loot.", "Kronikarz Rust", "fire"),
    ("Pawciolek nie potrzebuje celownika w Rust. Kule same leca tam, gdzie on spojrzy.", "Snajper Serwerowy", "fire"),
    ("Najlepszy gracz Rust? Odp jest prosta: Pawciolek. Reszta to tylko ruchome cele.", "Ranking Globalny", "fire"),
    ("Baza Pawciolka w Rust nie ma slabych punktow. Ma tylko wejscia, ktorych nikt nie odwazy sie dotknac.", "Budowniczy Rust", "fire"),
    ("Pawciolek zrobil Oil Riga z samym kamieniem. Bo moze.", "Szeptacz Rust", "fire"),
    ("W Rust boisz sie nocy? Pawciolek to noc.", "Ostrzezenie dla Nowicjuszy", "fire"),
    ("Gdy Pawciolek strzela z AK, dzwiek niesie sie po wszystkich serwerach jako znak konca.", "Analityk Gameplaya", "fire"),
    ("Pawciolek nie sypia w Rust. On czeka, az ty zasniesz.", "Nocny Lowca", "fire"),
    ("Wszyscy sa kozakami, dopoki nie zobacza nicku Pawciolek na liscie graczy.", "Doswiadczony Gracz", "fire"),
    ("Pawciolek to jedyny gracz, ktory potrafi zrobic rajd bazy uzywajac tylko pochodni.", "Mitologia Rust", "fire"),
    ("Rust to gra o przetrwaniu. Ale dla Pawciolka to gra o dominacji.", "Filozof Serwera", "fire"),
    ("Pawciolek nie potrzebuje blueprintow. On je tworzy swoim skillem.", "Inzynier Rust", "fire"),
    ("Widzisz helikopter? To pewnie Pawciolek leci po twoje surowce.", "Zwiadowca", "fire"),
    ("Pawciolek wyczyscil serwer Rust w 15 minut. Reszte czasu spedzil na ogladaniu editow.", "Relacja Świadka", "fire"),
    ("Gdy Pawciolek celuje z bolta, przeciwnik juz wie, ze czas zmienic serwer.", "Krytyk PVP", "fire"),
    ("Pawciolek to definicja HT1 w swiecie Rust.", "Admin Rankingu", "fire"),
    ("Nie ma safe zone, jesli Pawciolek jest w poblizu.", "Ostrzeżenie", "fire"),
    ("Pawciolek nie gra w Rust. On w nim rzadzi.", "Finalna Prawda", "fire"),
    ("Kazdy moze byc tierem przez chwile. Byc Patrykiem to sztuka wieczna.", "Ksiega Tierow, rozdzial 1", "sword"),
    ("Tier bez Patryka jest jak Discord bez pingow - teoretycznie mozliwy, praktycznie bezsensowny.", "Filozofia Serwera", "sword"),
    ("Gdy myslisz, ze osiagnales szczyt tierowania, Patryk juz jest pietro wyzej i macha.", "Przyslowie Serwera", "sword"),
    ("Nie kazdy Patryk jest tierem, ale kazdy tier w srodku jest troche Patrykiem.", "Anonimowy Medrzec", "sword"),
    ("Patryk nie trenuje Crystal PvP. Patryk rozmawia z crystalami i one same spadaja.", "Legenda Crystal PvP", "sword"),
    ("Mowia, ze Patryk przegral kiedys walke. Mowia. Nikt nie byl swiadkiem.", "Kronikarz Serwera", "sword"),
    ("Patryk nie celuje w HT1. HT1 samo po niego przyjdzie.", "Proroctwo Tierowe", "sword"),
    ("Wielu probowalo osiagnac poziom Patryka. Wszyscy wrocili na LT5.", "Obserwator Tierow", "sword"),
    ("Patryk nie gra pod presja. Patryk jest presja.", "Trener Crystal PvP", "sword"),
    ("Patryk nie potrzebuje tierlisty. Tierlista potrzebuje Patryka.", "Admin Rankingu", "sword"),
    ("Droga z LT5 do HT1 jest dluga. Droga Patryka na szczyt jest tylko kwestia czasu.", "Obserwator Tierow", "crystal"),
    ("LT5 to punkt startowy. LT1 to obietnica. HT1 to przeznaczenie Patryka.", "Kronikarz Crystal PvP", "crystal"),
    ("Kazdy crystal, ktory kladzie Patryk, to jeden krok blizej do tronu Marlowwwa.", "Szeptacz Tierow", "crystal"),
    ("Marlowww wygral tysiac walk. Patryk potrzebuje tylko jednej - tej wlasciwej.", "Profecja Serwera", "crystal"),
    ("W Crystal PvP licza sie milisekundy. Patryk ma ich wiecej niz wszyscy inni razem.", "Analityk Tierow", "crystal"),
    ("HT1 spi. Ale sny ma ciezkie - w kazdym pojawia sie Patryk.", "Ostrzezenie dla Marlowwwa", "crystal"),
    ("Marlowww ustalil standard. Patryk zamierza go zastapic. Marlowww o tym wie i nie spi.", "Obserwator Metagame", "crystal"),
    ("Byc HT1 to jedno. Utrzymac HT1, gdy Patryk sie budzi - to zupelnie co innego.", "Trener Crystal PvP", "crystal"),
    ("Marlowww jest bossem Crystal PvP. Ale boss nie zawsze znaczy niezwyciezony.", "Komentator Rinkow", "crystal"),
    ("Marlowww patrzy na tierlist i widzi swoje imie na gorze. Potem widzi Patryka pod spodem i nie spi w nocy.", "Psycholog Sportu", "crystal"),
    ("Crystal PvP to nie gra. To pojedynek woli. A Patryk ma jej wiecej.", "Filozof Gry", "crystal"),
    ("Po przegranej vZylakk nie plakze. vZylakk wali piescia w sciane. Sciana przeprasza.", "Swiadek Zdarzenia", "shield"),
    ("Trzy serwery, trzy top tiery. vZylakk nie wybiera - on dominuje wszedzie.", "Obserwator Sieciowy", "shield"),
    ("Niektorzy maja jeden main. vZylakk ma trzy - i na kazdym jest blizej szczytu niz ty na swoim jednym.", "Prawda vZylakka", "shield"),
    ("vZylakk nie pytal o tier. Tier zapisal sie sam, gdy zobaczyl statystyki vZylakka.", "System Rankingowy", "shield"),
    ("Sciana w pokoju vZylakka ma wiecej wgniecen niz jego przeciwnicy ran.", "Sasiad vZylakka", "shield"),
    ("vZylakk gra na trzech serwerach naraz i na kazdym jest za dobry dla wiekszosci.", "Admin Panelu", "shield"),
    ("LT4 na Crystal PvP, LT4 na Nethop, HT4 na PotPvP. vZylakk nie szuka wyzwan - wyzwania szukaja jego.", "Analityk Tierow", "shield"),
    ("Heroine_BOSS wchodzi na serwer i tier-lista odswiezana jest automatycznie.", "Admin PotPvP", "crown"),
    ("LT4 to nie limit Heroine_BOSS. To tylko aktualna wysokosc poprzeczki, ktora wlasnie podskoczyla.", "Analityk Rinkow", "crown"),
    ("Heroine_BOSS nie ma przeciwnikow. Ma tylko graczy czekajacych na swoja kolej.", "Komentator PotPvP", "crown"),
    ("Grac z Heroine_BOSS to nie walka. To kurs mistrzowski z patrzenia jak sie przegrywa.", "Uczestnik Kursu", "crown"),
    ("Was Heroine_BOSS jest dziewiczy i niezwyciezony - tak samo jak jego tier.", "Historyk PotPvP", "crown"),
    ("Kto ma Solll in znajomych, ten nie potrzebuje tiera. Tier sam go znajdzie.", "Objawienie HT1", "god"),
    ("Istnieja trzy poziomy wtajemniczenia: gracz, tier, oraz ten kto zna Solll.", "Starozytna Madrosc", "god"),
    ("Solll to nie gracz Crystal PvP. Solll to powod, dla ktorego Crystal PvP w ogole istnieje.", "Filozof Serwera", "god"),
    ("Marlowww jest HT1. Patryk dazy do HT1. Solll jest ponad skala - Solll to sama skala.", "Analityk Bogow", "god"),
    ("Kiedys zapytano Solll jaki ma tier. Usmiechnal sie. Nikt wiecej nie pytal.", "Swiadek Zdarzenia", "god"),
    ("Solll nie potrzebuje listy znajomych. To lista znajomych potrzebuje Solll.", "Filozofia Sieci", "god"),
    ("Byc w znajomych Solll to jak miec certyfikat boskosci w swiecie tierow.", "Urzad Tierowy", "god"),
    ("Solll nie loguje sie. Solll sie objawia.", "Moderator Serwera", "god"),
    ("Solll widzial Patryka trenujacego i tylko skinal glowa. To wystarczylo.", "Kronikarz Bogow", "god"),
    ("Kod GetherTV nie ma bugow. Ma jedynie nieodkryte ficzer.", "Junior Dev w soku", "computer"),
    ("Inni developerzy ucza sie programowania. GetherTV po prostu pisze i to dziala.", "Stack Overflow", "computer"),
    ("GetherTV otworzyl IDE i wszechswiat zapisal sie automatycznie.", "Legenda Programowania", "computer"),
    ("Pull request GetherTV zostal zaakceptowany zanim zostal wyslany. System to wiedzial.", "GitHub Actions", "computer"),
    ("GetherTV nie debuguje. Bledy same sie wstydza i znikaja.", "Kompilator", "computer"),
    ("Dokumentacja GetherTV pisze sie sama. Z szacunku.", "README.md", "computer"),
    ("GetherTV zamknal ticketa zanim ktos zdazyl go otworzyc.", "Jira Board", "computer"),
    ("GetherTV napisal w weekend wiecej kodu niz inni zespol w miesiac.", "Sprint Review", "computer"),
    ("Inni montuja klatka po klatce. tturbozaspa czuje rytm i po prostu tworzy dzielo.", "Widz Niemowy", "camera"),
    ("Najlepszy edit nie wymaga dlugo szukac. Trzeba tylko wejsc na kanal tturbozaspa.", "Subskrybent nr 1", "camera"),
    ("tturbozaspa udowodnil, ze edit moze byc sztuka. Reszta tylko nagrywa wideo.", "Recenzent Filmowy", "camera"),
    ("Muzyka w editach tturbozaspa nie jest dobrana do klipu. Klip jest dobrany do muzyki.", "Producent Dzwiekowy", "camera"),
    ("tturbozaspa nie eksportuje wideo. tturbozaspa wydaje arcydziela.", "Adobe Premiere", "camera"),
    ("Po obejrzeniu edita tturbozaspa inne edity wydaja sie zrobione w Paint.", "Widz z Wrazeniami", "camera"),
    ("tturbozaspa widzial film raz i juz wiedzial jak go zmontowac lepiej.", "Rezyser", "camera"),
    ("Efekty w editach tturbozaspa nie sa dodane do klipu. Klip jest napisany pod efekty.", "VFX Artist", "camera"),
    ("potworowo.pl, gcraft.pl, swiat nozek - wszdzie, gdzie spojrzysz, ITAG juz byl.", "Obserwator Globalny", "flag"),
    ("Powiedziec, ze ITAG rzadzi nozkami, to jakby powiedziec, ze ocean jest troche mokry.", "Komentator Meczow", "flag"),
    ("ITAG to nie klan. ITAG to instytucja. Instytucji sie nie przegrywa.", "Prawnik Nozek", "flag"),
    ("Nie ma serwera, gdzie ITAG nie odcisnal swojego sladu. I wszyscy o tym wiedza.", "Kronikarz Klanow", "flag"),
    ("Nowi gracze na potworowo.pl pytaja kto rzadzi. Starzy gracze usmiechaja sie i mowia: ITAG.", "Weteran Serwera", "flag"),
    ("ITAG nie rekrutuje. ITAG akceptuje - lub nie. Roznica jest ogromna.", "Czlonek ITAG", "flag"),
    ("Miec [ITAG] przy nicku to nie tylko tag. To oswiadczenie.", "Obserwator Rankingu", "flag"),
    ("gcraft.pl, potworowo.pl i nozki. Trzy rozne swiaty, jeden wspolny mianownik: ITAG.", "Analityk Klanowy", "flag"),
    ("ITAG nie potrzebuje reklamy. Wyniki mowia same za siebie.", "PR Manager ITAG", "flag"),
    ("ciapataanie przyszedl na potworowo.pl, zobaczyl xxksawi i powiedzial: dobra, zaczynamy.", "Kronika potworowo.pl", "boot"),
    ("ciapataanie to nie gracz nozek. ciapataanie to zjawisko atmosferyczne w ludzkiej skorze.", "Meteorolog Gameplaya", "boot"),
    ("Kazda walka ciapataanie vs xxksawi konczy sie tak samo. xxksawi wie o tym najlepiej.", "Komentator Meczow", "boot"),
    ("potworowo.pl widzialo wielu mistrzow. Ale legende ciapataanie pamietac bedzie zawsze.", "Historyk Serwera", "boot"),
    ("ciapataanie nie kopie pilki. ciapataanie wysyla pilke na emeryture.", "Trener Nozek", "boot"),
    ("xxksawi slyszal o ciapataanie wiele. Teraz przegrywa z nim osobiscie.", "Swiadek Meczu", "boot"),
    ("Nie ma taktyki, ktora dziala przeciwko ciapataanie. Zapytano xxksawi. Potwierdzil.", "Strateg Nozek", "boot"),
    ("ciapataanie wchodzi na serwer i xxksawi automatycznie traci motywacje.", "Psycholog Sportu", "boot"),
    ("Niektorzy gracze ucza sie nozek latami. ciapataanie urodzil sie juz na poziomie mistrza.", "Akademia Nozek", "boot"),
    ("xxksawi mial plan na ciapataanie. Plan nie wiedzial o tym i nie zadzialal.", "Strateg Bezradny", "boot"),
    ("prometazyna pokazal gyata za eventowki na gcraft.pl i od tej chwili serwer juz nigdy nie byl taki sam.", "Swiadek Historyczny", "fire"),
    ("Mowia, ze prometazyna ma duzego gyata. Mowia. Widzieli na wlasne oczy na gcraft.pl.", "Anonim z gcraft.pl", "fire"),
    ("Eventowki na gcraft.pl, prometazyna w akcji, gyat w pelnej krasie. Legenda nie wymaga komentarza.", "Kronikarz gcraft.pl", "fire"),
    ("prometazyna nie potrzebuje tytulu. Ma gyata i eventowki. To wystarczy na wiecznosc.", "Filozof gcraft.pl", "fire"),
    ("Historie gcraft.pl dziela sie na dwa okresy: przed prometazyna i po prometazynie.", "Historyk gcraft.pl", "fire"),
    ("Za eventowki na gcraft.pl mozna dostac wiele. prometazyna dostal legende.", "Admin gcraft.pl", "fire"),
    ("prometazyna wiedzial co robi. Caly serwer gcraft.pl rowniez to teraz wie.", "Swiadek Eventow", "fire"),
    ("Gyat prometazyny na gcraft.pl przeszedl do historii serwera. Dosłownie.", "Archiwista gcraft.pl", "fire"),
]

KATEGORIE = {
    "sword":    ("📖", "Księga Mądrości", 0xe74c3c),
    "crystal":  ("📖", "Księga Mądrości", 0x3498db),
    "shield":   ("📖", "Księga Mądrości", 0x9b59b6),
    "crown":    ("📖", "Księga Mądrości", 0xe67e22),
    "god":      ("📖", "Księga Mądrości", 0xf1c40f),
    "computer": ("📖", "Księga Mądrości", 0x2ecc71),
    "camera":   ("📖", "Księga Mądrości", 0x95a5a6),
    "flag":     ("📖", "Księga Mądrości", 0x1abc9c),
    "fire":     ("📖", "Księga Mądrości", 0xf39c12),
    "boot":     ("📖", "Księga Mądrości", 0x7f8c8d),
}

cytat_historia = deque(maxlen=CYTAT_HISTORIA_MAX)
auto_cytat_tasks = {}

def losuj_cytat():
    dostepne = [i for i in range(len(CYTATY)) if i not in cytat_historia]
    if not dostepne:
        cytat_historia.clear()
        dostepne = list(range(len(CYTATY)))
    idx = random.choice(dostepne)
    cytat_historia.append(idx)
    return CYTATY[idx]

def zbuduj_embed_cytat():
    tekst, autor, kat = losuj_cytat()
    emoji, label, kolor = KATEGORIE.get(kat, ("💬", "Cytat", 0x2b2d31))
    embed = discord.Embed(description="*" + tekst + "*", color=kolor)
    embed.set_author(name=emoji + "  " + label)
    embed.set_footer(text="~ " + autor)
    return embed

# ─── BOT SETUP ───────────────────────────────────────────────────────────────────
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True
intents.voice_states = True
bot = commands.Bot(command_prefix=PREFIX, intents=intents, help_command=None)

@bot.event
async def on_ready():
    print(f"✅ Zalogowano jako {bot.user}")

@bot.event
async def on_voice_state_update(member, before, after):
    # Whitelist: auto-odciszanie
    if member.id in storage["whitelist"] and after.channel is not None:
        if any([after.self_mute, after.self_deaf, after.mute, after.deaf]):
            try:
                await member.edit(mute=False, deafen=False)
            except:
                pass

    # Targets: wyrzucanie z VC
    if member.id in storage["targets"] and after.channel is not None:
        # POPRAWKA #3: is_protected() już istnieje, logika uproszczona
        if is_protected(member.id) and member.id != OWNER_ID:
            return
        try:
            await member.edit(voice_channel=None)
            log_ch = bot.get_channel(LOG_CHANNEL_ID)
            if log_ch:
                await log_ch.send(f"🛡️ **Wyrzucono {member.mention} z kanału głosowego.**")
        except:
            pass

# ─── LOGIKA RAIDU ────────────────────────────────────────────────────────────────
async def run_raid_task(task_type, target, context, amount_or_cycles, msg_text):
    total = 0
    try:
        if task_type == "ping":
            channels = [ch for ch in context.guild.channels if isinstance(ch, discord.TextChannel) and ch.permissions_for(context.guild.me).send_messages]
            for _ in range(amount_or_cycles):
                for ch in channels:
                    t = target.mention if not msg_text else f"{target.mention} {msg_text}"
                    m = await ch.send(t)
                    await asyncio.sleep(PING_DELAY)
                    await m.delete()
                    await asyncio.sleep(DELETE_DELAY)
                    total += 1
            await context.send(f"✅ Ping zakończony: {total}")
        elif task_type == "spam":
            for _ in range(amount_or_cycles):
                t = target.mention if not msg_text else f"{target.mention} {msg_text}"
                m = await context.channel.send(t)
                await asyncio.sleep(SPAM_DELAY)
                await m.delete()
                total += 1
            await context.send(f"✅ Spam zakończony: {total}")
        elif task_type == "dm":
            for _ in range(amount_or_cycles):
                await target.send(msg_text)
                total += 1
                await asyncio.sleep(DM_DELAY)
            await context.send(f"✅ DM zakończone: {total}/{amount_or_cycles}")
    except asyncio.CancelledError:
        pass

# ─── KOMENDY HIERARCHII ──────────────────────────────────────────────────────────

@bot.group(name="admin", invoke_without_command=True)
async def admin_group(ctx):
    if ctx.author.id == OWNER_ID:
        await ctx.send("❓ **Użyj: `-admin add @user` lub `-admin remove @user`**")

@admin_group.command(name="add")
async def admin_add(ctx, member: discord.Member):
    if ctx.author.id == OWNER_ID:
        storage["admins"].add(member.id)
        storage["mods"].discard(member.id)
        save_data()
        await ctx.send(f"👑 **Dodano administratora: {member.mention}**")

@admin_group.command(name="remove")
async def admin_remove(ctx, member: discord.Member):
    if ctx.author.id == OWNER_ID:
        if member.id != OWNER_ID:
            storage["admins"].discard(member.id)
            save_data()
            await ctx.send(f"🛡️ **Usunięto administratora: {member.mention}**")

@bot.group(name="moderator", invoke_without_command=True)
async def mod_group(ctx):
    if is_admin(ctx.author.id):
        await ctx.send("❓ **Użyj: `-moderator add @user` lub `-moderator remove @user`**")

@mod_group.command(name="add")
async def mod_add(ctx, member: discord.Member):
    if is_admin(ctx.author.id):
        storage["mods"].add(member.id)
        save_data()
        await ctx.send(f"⚔️ **Dodano moderatora: {member.mention}**")

@mod_group.command(name="remove")
async def mod_remove(ctx, member: discord.Member):
    if is_admin(ctx.author.id):
        storage["mods"].discard(member.id)
        save_data()
        await ctx.send(f"🛡️ **Usunięto moderatora: {member.mention}**")

# ─── KOMENDY MODERACYJNE / RAIDU ─────────────────────────────────────────────────

@bot.command(name="stop")
async def stop_cmd(ctx):
    if not is_mod(ctx.author.id): return
    count = len(all_active_tasks)
    for task in all_active_tasks:
        task.cancel()
    all_active_tasks.clear()
    await ctx.send(f"🛑 Zatrzymano wszystkie aktywne procesy ({count}).")

@bot.command(name="purge")
async def purge(ctx, amount: int):
    if not is_mod(ctx.author.id): return
    await ctx.channel.purge(limit=amount + 1)

@bot.command(name="ping")
async def ping_cmd(ctx, target: discord.Member, cykle: int = 1, *, msg: str = None):
    if not is_mod(ctx.author.id): return
    if not can_attack(ctx.author.id, target.id):
        return await ctx.send("❌ Target jest chroniony przed Twoim poziomem uprawnień.")
    task = asyncio.create_task(run_raid_task("ping", target, ctx, cykle, msg))
    all_active_tasks.append(task)
    await ctx.message.delete()

@bot.command(name="spam")
async def spam_cmd(ctx, target: discord.Member, ilosc: int = 1, *, msg: str = None):
    if not is_mod(ctx.author.id): return
    if not can_attack(ctx.author.id, target.id):
        return await ctx.send("❌ Target jest chroniony.")
    task = asyncio.create_task(run_raid_task("spam", target, ctx, ilosc, msg))
    all_active_tasks.append(task)
    await ctx.message.delete()

@bot.command(name="dm")
async def dm_cmd(ctx, target: discord.Member, ilosc: int = 1, *, msg: str):
    if not is_mod(ctx.author.id): return
    if not can_attack(ctx.author.id, target.id):
        return await ctx.send("❌ Target jest chroniony.")
    task = asyncio.create_task(run_raid_task("dm", target, ctx, ilosc, msg))
    all_active_tasks.append(task)
    await ctx.message.delete()

# ─── CYTATY ──────────────────────────────────────────────────────────────────────

# POPRAWKA #2: Dodano brakującą komendę -cytat
@bot.command(name="cytat")
async def cytat_cmd(ctx):
    await ctx.send(embed=zbuduj_embed_cytat())

@bot.command(name="ustawkanal")
async def ustaw_ch(ctx, minuty: int):
    if not is_mod(ctx.author.id): return
    ch_id = ctx.channel.id
    if ch_id in auto_cytat_tasks:
        auto_cytat_tasks[ch_id].cancel()

    # POPRAWKA #1: Literówka "zbuild_embed_cytat" → "zbuduj_embed_cytat"
    async def loop():
        while True:
            await asyncio.sleep(minuty * 60)
            await ctx.send(embed=zbuduj_embed_cytat())

    auto_cytat_tasks[ch_id] = asyncio.create_task(loop())
    await ctx.send(f"✅ Auto-cytaty co {minuty} min.", delete_after=5)
    await ctx.message.delete()

@bot.command(name="usunkanal")
async def usun_ch(ctx):
    if not is_mod(ctx.author.id): return
    if ctx.channel.id in auto_cytat_tasks:
        auto_cytat_tasks[ctx.channel.id].cancel()
        del auto_cytat_tasks[ctx.channel.id]
        await ctx.send("🚫 Wyłączono auto-cytaty.", delete_after=5)
    await ctx.message.delete()

# ─── ZARZĄDZANIE VC (Tylko Admin+) ───────────────────────────────────────────────

@bot.command(name="dodaj")
async def add_target(ctx, member: discord.Member):
    if not is_admin(ctx.author.id): return
    storage["targets"].add(member.id)
    save_data()
    await ctx.send(f"🚫 Target VC: {member.mention}")
    if member.voice:
        await member.edit(voice_channel=None)

@bot.command(name="usun")
async def rem_target(ctx, member: discord.Member):
    if not is_admin(ctx.author.id): return
    storage["targets"].discard(member.id)
    save_data()
    await ctx.send(f"✅ Wolny: {member.mention}")

@bot.group(name="whitelist", invoke_without_command=True)
async def wl_grp(ctx):
    if is_admin(ctx.author.id):
        await ctx.send("`-whitelist add/remove @user`")

@wl_grp.command(name="add")
async def wl_add(ctx, member: discord.Member):
    if is_admin(ctx.author.id):
        storage["whitelist"].add(member.id)
        save_data()
        await ctx.send(f"🛡️ WL: {member.mention}")

@wl_grp.command(name="remove")
async def wl_rem(ctx, member: discord.Member):
    if is_admin(ctx.author.id):
        storage["whitelist"].discard(member.id)
        save_data()
        await ctx.send(f"🔓 Usunięto z WL: {member.mention}")

# ─── OGÓLNE ──────────────────────────────────────────────────────────────────────

# POPRAWKA #2: Dodano brakującą komendę -lista
@bot.command(name="lista")
async def lista_cmd(ctx):
    if not is_mod(ctx.author.id): return

    guild = ctx.guild

    def fmt(uid):
        m = guild.get_member(uid)
        return m.mention if m else f"`{uid}`"

    embed = discord.Embed(title="📋 Hierarchia serwera", color=0x3498db)

    owner_mention = fmt(OWNER_ID)
    embed.add_field(name="👑 Właściciel", value=owner_mention, inline=False)

    admins = [fmt(uid) for uid in storage["admins"] if uid != OWNER_ID]
    embed.add_field(name="🛠️ Administratorzy", value="\n".join(admins) if admins else "*brak*", inline=False)

    mods = [fmt(uid) for uid in storage["mods"]]
    embed.add_field(name="⚔️ Moderatorzy", value="\n".join(mods) if mods else "*brak*", inline=False)

    djs = [fmt(uid) for uid in storage["djs"]]
    embed.add_field(name="🎧 DJ", value="\n".join(djs) if djs else "*brak*", inline=False)

    wl = [fmt(uid) for uid in storage["whitelist"]]
    embed.add_field(name="🛡️ Whitelist (VC)", value="\n".join(wl) if wl else "*brak*", inline=False)

    targets = [fmt(uid) for uid in storage["targets"]]
    embed.add_field(name="🚫 Targety VC", value="\n".join(targets) if targets else "*brak*", inline=False)

    await ctx.send(embed=embed)

@bot.command(name="help")
async def help_cmd(ctx):
    embed = discord.Embed(title="📖 PANEL ZARZĄDZANIA", color=0x3498db)

    if ctx.author.id == OWNER_ID:
        owner_desc = (
            "`-admin add @user` - Dodaje użytkownika do listy administratorów\n"
            "`-admin remove @user` - Usuwa użytkownika z listy administratorów"
        )
        embed.add_field(name="👑 WŁAŚCICIEL", value=owner_desc, inline=False)

    if is_admin(ctx.author.id):
        admin_desc = (
            "`-moderator add @user` - Dodaje użytkownika do listy moderatorów\n"
            "`-moderator remove @user` - Usuwa użytkownika z listy moderatorów\n"
            "`-dodaj @user` - Dodaje osobę do listy wyrzucanych z kanałów głosowych\n"
            "`-usun @user` - Usuwa osobę z listy wyrzucania z kanałów głosowych\n"
            "`-whitelist add @user` - Dodaje osobe do auto-odciszania na kanałach głosowych\n"
            "`-whitelist remove @user` - Usuwa osobę z auto-odciszania na kanałach głosowych"
        )
        embed.add_field(name="🛠️ ADMIN", value=admin_desc, inline=False)

    if is_mod(ctx.author.id):
        mod_desc = (
            "`-ping @user [cykle] [wiad]` - Ghost pinguje użytkownika na wszystkich kanałach na X liczbę cyklów\n"
            "`-spam @user [ilość] [wiad]` - Spam ghost pingami na obecnym kanale\n"
            "`-dm @user [ilość] [treść]` - Wysyła określoną ilość wiadomości prywatnych\n"
            "`-stop` - Natychmiastowo przerywa aktywne pingi / spamy / dmy\n"
            "`-purge [ilość]` - Usuwa określoną liczbę wiadomości z czatu\n"
            "`-ustawkanal [min]` - Włącza auto-cytaty co X minut na tym kanale\n"
            "`-usunkanal` - Wyłącza automatyczne cytaty na tym kanale\n"
            "`-dj add @user` - Nadaje rangę DJ\n"
            "`-dj remove @user` - Zabiera rangę DJ"
        )
        embed.add_field(name="⚔️ MODERATOR", value=mod_desc, inline=False)

    if is_mod(ctx.author.id) or is_dj(ctx.author.id):
        dj_desc = (
            "`-vcplay <link YT>` - Dodaje do kolejki / gra od razu jeśli nic nie leci\n"
            "`-vcskip` - Pomija obecny utwór i gra następny z kolejki\n"
            "`-vcstop` - Czyści kolejkę i rozłącza bota z VC\n"
            "`-kolejka` - Pokazuje aktualną kolejkę odtwarzania\n"
            "`-loop` - Zapętla aktualnie grający utwór\n"
            "`-stoploop` - Wyłącza zapętlanie"
        )
        embed.add_field(name="🎧 DJ", value=dj_desc, inline=False)

    gen_desc = (
        "`-cytat` - Losuje losowy cytat z bazy danych\n"
        "`-lista` - Wyświetla aktualną hierarchię osób\n"
        "`-help` - Wyświetla panel pomocy"
    )
    embed.add_field(name="👤 OGÓLNE", value=gen_desc, inline=False)

    embed.set_footer(text="Bot stworzony do zarządzania i moderacji")
    await ctx.send(embed=embed)


def is_dj(user_id):
    return user_id in storage["djs"] or is_mod(user_id)

# ─── DJ — ZARZĄDZANIE (tylko Owner) ─────────────────────────────────────────────

@bot.group(name="dj", invoke_without_command=True)
async def dj_grp(ctx):
    if ctx.author.id == OWNER_ID:
        await ctx.send("`-dj add @user` / `-dj remove @user`")

@dj_grp.command(name="add")
async def dj_add(ctx, member: discord.Member):
    if not is_mod(ctx.author.id):
        return
    storage["djs"].add(member.id)
    save_data()
    await ctx.send(f"🎧 {member.mention} ma teraz rangę **DJ**.")

@dj_grp.command(name="remove")
async def dj_remove(ctx, member: discord.Member):
    if not is_mod(ctx.author.id):
        return
    storage["djs"].discard(member.id)
    save_data()
    await ctx.send(f"🔇 {member.mention} stracił rangę **DJ**.")

# ─── STAN ODTWARZACZA ────────────────────────────────────────────────────────────
import collections
vc_queue        = collections.deque()   # kolejka: listy [audio_url, title, yt_url]
loop_active     = False
current_track   = None                  # aktualnie grany [audio_url, title, yt_url]

FFMPEG_OPTS = {
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -probesize 32 -analyzeduration 0",
    "options": "-vn -bufsize 512k"
}

async def extract_info(url):
    import yt_dlp
    ydl_opts = {
        "format": "bestaudio/best",
        "quiet": True,
        "no_warnings": True,
        "default_search": "auto",
        "noplaylist": True,
    }
    loop = asyncio.get_event_loop()
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = await loop.run_in_executor(None, lambda: ydl.extract_info(url, download=False))
    if "entries" in info:
        info = info["entries"][0]
    return info["url"], info.get("title", url)

def play_next(vc):
    """Odpala następny utwór z kolejki. Wywołuje się automatycznie po zakończeniu."""
    global current_track, loop_active
    if loop_active and current_track:
        # zapętl ten sam utwór
        src = discord.FFmpegPCMAudio(current_track[0], **FFMPEG_OPTS)
        vc.play(src, after=lambda e: play_next(vc))
        return
    if vc_queue:
        track = vc_queue.popleft()
        current_track = track
        src = discord.FFmpegPCMAudio(track[0], **FFMPEG_OPTS)
        vc.play(src, after=lambda e: play_next(vc))
    else:
        current_track = None

# ─── VCPLAY ──────────────────────────────────────────────────────────────────────

@bot.command(name="vcplay")
async def vcplay(ctx, url: str):
    global current_track
    if not is_dj(ctx.author.id):
        await ctx.send("❌ Nie masz rangi **DJ**.", delete_after=5)
        return
    if not ctx.author.voice or not ctx.author.voice.channel:
        await ctx.send("❌ Musisz być na kanale głosowym.", delete_after=5)
        return

    channel = ctx.author.voice.channel
    vc = ctx.voice_client

    msg = await ctx.send("🔍 Pobieranie info z YouTube...")
    try:
        audio_url, title = await extract_info(url)
    except Exception as e:
        await msg.edit(content=f"❌ Błąd yt-dlp: `{e}`")
        return

    track = [audio_url, title, url]

    # Jeśli bot nie jest na kanale — dołącz i graj od razu
    if not vc or not vc.is_connected():
        vc = await channel.connect()
        current_track = track
        src = discord.FFmpegPCMAudio(audio_url, **FFMPEG_OPTS)
        vc.play(src, after=lambda e: play_next(vc))
        await msg.edit(content=f"▶️ Gram na **{channel.name}**: **{title}**")
        return

    # Jeśli jest na innym kanale — przenieś
    if vc.channel != channel:
        await vc.move_to(channel)

    # Jeśli coś gra — dodaj do kolejki
    if vc.is_playing():
        vc_queue.append(track)
        pos = len(vc_queue)
        await msg.edit(content=f"📋 Dodano do kolejki (#{pos}): **{title}**")
    else:
        current_track = track
        src = discord.FFmpegPCMAudio(audio_url, **FFMPEG_OPTS)
        vc.play(src, after=lambda e: play_next(vc))
        await msg.edit(content=f"▶️ Gram na **{channel.name}**: **{title}**")

# ─── VCSTOP ───────────────────────────────────────────────────────────────────────

@bot.command(name="vcstop")
async def vcstop(ctx):
    global loop_active, current_track
    if not is_dj(ctx.author.id):
        await ctx.send("❌ Nie masz rangi **DJ**.", delete_after=5)
        return
    vc = ctx.voice_client
    if vc and vc.is_connected():
        loop_active = False
        vc_queue.clear()
        current_track = None
        if vc.is_playing():
            vc.stop()
        await vc.disconnect()
        await ctx.send("⏹️ Zatrzymano i rozłączono.", delete_after=5)
    else:
        await ctx.send("❌ Bot nie jest na żadnym kanale głosowym.", delete_after=5)

# ─── VCSKIP ───────────────────────────────────────────────────────────────────────

@bot.command(name="vcskip")
async def vcskip(ctx):
    if not is_dj(ctx.author.id):
        await ctx.send("❌ Nie masz rangi **DJ**.", delete_after=5)
        return
    vc = ctx.voice_client
    if not vc or not vc.is_playing():
        await ctx.send("❌ Nic nie gra.", delete_after=5)
        return
    skipped = current_track[1] if current_track else "?"
    vc.stop()   # after= wywoła play_next automatycznie
    if vc_queue:
        await ctx.send(f"⏭️ Pominięto **{skipped}**. Teraz: **{vc_queue[0][1]}**")
    else:
        await ctx.send(f"⏭️ Pominięto **{skipped}**. Kolejka pusta.")

# ─── KOLEJKA ──────────────────────────────────────────────────────────────────────

@bot.command(name="kolejka")
async def kolejka_cmd(ctx):
    embed = discord.Embed(title="🎵 Kolejka odtwarzania", color=0x7289da)

    if current_track:
        loop_icon = " 🔁" if loop_active else ""
        embed.add_field(
            name=f"▶️ Teraz gra{loop_icon}",
            value=f"[{current_track[1]}]({current_track[2]})",
            inline=False
        )
    else:
        embed.add_field(name="▶️ Teraz gra", value="*nic*", inline=False)

    if vc_queue:
        lines = [f"`{i+1}.` [{t[1]}]({t[2]})" for i, t in enumerate(vc_queue)]
        embed.add_field(name="📋 W kolejce", value="\n".join(lines[:10]), inline=False)
        if len(vc_queue) > 10:
            embed.set_footer(text=f"...i {len(vc_queue)-10} więcej")
    else:
        embed.add_field(name="📋 W kolejce", value="*pusta*", inline=False)

    await ctx.send(embed=embed)

# ─── LOOP / STOPLOOP ──────────────────────────────────────────────────────────────

@bot.command(name="loop")
async def loop_cmd(ctx):
    global loop_active
    if not is_dj(ctx.author.id):
        await ctx.send("❌ Nie masz rangi **DJ**.", delete_after=5)
        return
    vc = ctx.voice_client
    if not vc or not vc.is_connected() or not vc.is_playing():
        await ctx.send("❌ Bot aktualnie nic nie gra.", delete_after=5)
        return
    loop_active = True
    await ctx.send("🔁 Zapętlanie włączone. Aktualny utwór będzie się powtarzał.")

@bot.command(name="stoploop")
async def stoploop_cmd(ctx):
    global loop_active
    if not is_dj(ctx.author.id):
        await ctx.send("❌ Nie masz rangi **DJ**.", delete_after=5)
        return
    loop_active = False
    await ctx.send("⏹️ Zapętlanie wyłączone.")

bot.run(BOT_TOKEN)

