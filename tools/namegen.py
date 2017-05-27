from random import choice

l1 = ["Mech", "Gun ", "Ultimate ", "Kitten", "Horse ", "Pony ",
    "Forest ", "Invasion ", "Guild ", "Speed", "World of ", "Space ",
    "Outlands ", "Noble ", "Kingdom ", "Holy ", "Eternal ", "Power ",
    "Petty ", "Heroic ", "Final ", "Mom's ", "Incredible ", "Monkey",
    "Color ", "Fire ", "Dimension ", "Home ", "Office ", "Shadow",
    "Infinite ", "Boundless ", "Disturbing ", "Glorious ", "Cold ",
    "Infamous ", "Honorable ", "Evil ", "US ", "Endless ", "American ",
    "Alliance ", "Cow ", "Student ", "Pretty ", "Dungeon ", "Border ",
    "The King's ", "Pirate ", "Ninja ", "World ", "Core ", "Realm ",
    "Fish ", "Deep Water ", "Shark ", "Air ", "Monster ", "Silent ",
    "Unholy ", "Tiny ", "The ", "Dragon ", "Undead ", "Blood ", "Mystic ",
    "Lemming ", "Big Wheel ", "Vampire ", "Werewolf ", "Elder ", "Steam ",
    "Batman's ", "Boy Scout ", "Pixel ", "Maximum ", "Great ",
    "Penultimate ", "UX-", "Proto", "Meth", "Drug ", "Mob ", "Gang ",
    "Zombie ", "Clone ", "Boob ", "Swimsuit ", "Hockey ", "Curling ",
    "Drugrunner's ", "Sparky's ", "Weebler's ", "Ever", "Fishing ",
    "Photo", "Code ", "Digital ", "Amazing "]

l2 = ["Wars", "Warrior", "Fighter", "Sim", "Showdown", "Flight",
    "Enemies", "Slaughter", "Honors", "Planning", "Secretary", "Power",
    "Danger", "Revenge", "Run", "Race", "Transport", "Wilds", "Planking",
    "Storm", "Fantasy", "Demise", "Hospital", "Revolution", "Prophecy",
    "Galaxy", "Quest", "Grounds", "Kingdoms", "Fortress", "Campaign",
    "Camping", "Party", "Destruction", "Army", "Bombing", "Distraction",
    "Economy", "Banking", "Defenders", "Lands", "Legends", "Olympics",
    "Horrors", "School", "Dream", "Deity", "Glory", "Lowlands", "Control",
    "Disaster", "Nightmare", "Fiend", "Attack", "Training", "Armageddon",
    "Dancers", "Skating", "Stone", "Hunter", "Wizard", "Knight", "Devil",
    "Depot", "Wing", "Creed", "Account", "Floors", "Boots", "Shooting",
    "Hunting", "Underpants", "Farming", "Countdown" , "Tactics", "Flower",
    "Express"]

l3 = ["", "Online", "2000", "3000", "2010", "Story", "Forever",
    ": The Sequel", "Redoux", ": The Sequel","Maximum Edition",
    ": The Prequel", "of Doom", "HD", "Saga", "Offline", "of Hope",
    "SD", "LXXVII", ": The Videogame",": Over 9000", ": Remake",
    ": Blood!", ": Magic", ": Gold edition", "Chronicles",
    ": Special Edition", ": Pit jumping", "Stories", "VI", "League",
    "Tales", "Extended Edition", ": The Wedding", "2012",
    "V", "3", "Ultra", "- Piecemaker", ": World's End", ": Hero",
    "of Time", "the Planning", ": Reckoning", ": Jabberwocky", ": Sleuth",
    ": Sorcery", ": Mathemagic",": More Money", "the Third",
    "of Toads", ": Snake eater!", ": The Pickening", ": Otto's Struggle"
    ]

pl31 = ["II", "III", "2", "Unlimited", "Deluxe", "Limited"]
pl32 = ["More Teeth", "The Gerbils", "The Goodness", "The Evil",
    "The Curse", "Sausagefest", "Reboot", "Magic", "More Feet",
    "Bananas!", "He's back!", "Double Truble", "Infinity!", "The Horror",
    "Robotastic!", "The Legend", "Mercat", "Greebo is Back!", "The Bad",
    "It never ends!", "Fun With Numbers!", "It's Dangerous", "She's Back!",
    "Outdoor Grilling", "Hippopotamus!", "Where others failed", "Nekomancer",
    "It's Gooby time!", "The Rift", "The Rainbow People", "Overtime!",
    "The Kittening", "It's PLAY time!"]

for x in pl31:
    for y in pl32:
        l3.append(x)
        l3.append("")
        l3.append("%s: %s" % (x, y))


p1 = ["Sweet", "Crappy", "Ludicrus", "Cool", "Warm", "Nice", "Terrible", "Vibrant", "Good", "Awesome", "Terrible", "Epic", "Simple", "Wicked", "Sharp", "Beautiful", ]
p2 = ["Preset", "Settings", "Display", "Look", "Configuration", "Looks", "Colors", " and bright", "and dark"]

def count_gamenames():
    return len(set(l1)) * len(set(l2)) * len(set(l3))

def make_gamename():
    t1 = "%s%s" % (choice(l1), choice(l2))
    r = choice(l3)
    if not r.startswith(":"):
        t1 = t1 + " "
    t1 = t1 + r
    return t1.strip()

def make_preset():
    return "%s %s" % (choice(p1), choice(p2))

