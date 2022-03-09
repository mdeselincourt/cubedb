import sqlite3
import itertools
import sys # Useful to have for sys.exit()

## Utility functions

def invertColourTuple(colourTuple):
    inverse = ["W","U","B","R","G"]
    for c in colourTuple:
        #print("Removing", c ,"from", inverse)
        inverse.remove(c)
    return inverse

## DB connection

connection = sqlite3.connect('cubedb.sqlite')
cursor = connection.cursor()
cursor2 = connection.cursor()

colours = ["W","U","B","R","G"]
shardsAndWedges = list(itertools.combinations(colours, r=3))
# print(shardsAndWedges)
colourPairs = list(itertools.combinations(colours, r=2))
synergies = []

# Find all the "colour pairs" as defined by NOT IN THE OTHER THREE (so that colourless are included)
for c1, c2, c3 in shardsAndWedges:

    (p1,p2) = invertColourTuple((c1,c2,c3))

    query = '''SELECT
        '{c1}{c2}{c3}',
        Synergies.Synergy,
        COUNT(CASE WHEN Synergies.RolePlayed='Payoff' THEN 1 END) as Payoffs, 
        COUNT(CASE WHEN Synergies.RolePlayed='Participant' THEN 1 END) as Participants,
        (COUNT(CASE WHEN Synergies.RolePlayed='Payoff' THEN 1 END) * COUNT(CASE WHEN Synergies.RolePlayed='Participant' THEN 1 END)) as Product 
    FROM Synergies
    INNER JOIN Cards ON Cards.Card=Synergies.Card
    WHERE (Cards.{c1} IS NULL AND Cards.{c2} IS NULL AND Cards.{c3} IS NULL) 
    --AND (Cards.{p1} = 1 OR Cards.{p2} = 1) -- This expression has been replaced by exclusion of the other three colours
    AND (Cards.Copies > 0)
    GROUP BY Synergies.Synergy
    ORDER BY (COUNT(CASE WHEN Synergies.RolePlayed='Payoff' THEN 1 END) * COUNT(CASE WHEN Synergies.RolePlayed='Participant' THEN 1 END)) DESC;'''.format(c1=c1,c2=c2,c3=c3,p1=p1,p2=p2)

    # Append each valid result to the array of synergies
    for synergyTuple in cursor.execute(query):
        if (synergyTuple[4] > 0):
            synergies.append((''.join(invertColourTuple(tuple(synergyTuple[0]))), synergyTuple[1], synergyTuple[2], synergyTuple[3], synergyTuple[4]))

# Convenience shorthand
def synergyScore(synergyTuple):
    return synergyTuple[4]

# Sort the synergies most supported first
synergies.sort(key=synergyScore,reverse=True)

# Reverse-engineer each synergy in order to describe it:

# Synergies (e.g. "WB Lifegain")
## Member groups (e.g. "White Payoffs")
### Cards (e.g. "Ajani's Pridemate")

synergiesLines = []

def stringifyTuple(tuple):
    return ';'.join(map(str,tuple))

# Reverse engineer each synergy in order to describe it
for syn in synergies:
    
    synergyLine = stringifyTuple(syn)

    # Log a line for just the synergy
    # synergiesLines.append("synergy;" + synergyLine)
    
    synname = syn[1]
    (p1,p2)=tuple(syn[0])
    (x1,x2,x3)=invertColourTuple((p1,p2))
    # Get a summary of the member groups of this synergy
    query = '''SELECT 
            --Synergies.Card, 
            Colour, 
            RolePlayed,
            COUNT(Synergies.Card) as cards
        FROM Synergies
        INNER JOIN Cards on Cards.Card=Synergies.Card
        WHERE Synergies.Synergy='{synname}'
        --AND (Cards.{p1} = 1 OR Cards.{p2} = 1) 
        AND Cards.{x1} IS NULL AND Cards.{x2} IS NULL AND Cards.{x3} IS NULL
        AND Cards.Copies > 0
        GROUP BY Colour, RolePlayed
        ORDER BY Colour       
        '''.format(synname=synname,p1=p1,p2=p2,x1=x1,x2=x2,x3=x3)

    # Get all the cards in this member group
    for memberGroupTuple in cursor.execute(query):
        memberGroupLine = stringifyTuple(memberGroupTuple)
        
        # Log a line for the group and its synergy
        # synergiesLines.append("group;" + synergyLine + ";" + memberGroupLine)
                
        groupColours = memberGroupTuple[0]
        groupRole = memberGroupTuple[1]
        
        query2 = '''SELECT 
            Synergies.Card, 
            Colour
        FROM Synergies
        INNER JOIN Cards on Cards.Card=Synergies.Card
        WHERE Synergies.Synergy='{synname}'
        AND Cards.Colour = '{groupColours}'
        AND Synergies.RolePlayed = '{groupRole}'
        --AND (Cards.{p1} = 1 OR Cards.{p2} = 1) 
        AND Cards.{x1} IS NULL AND Cards.{x2} IS NULL AND Cards.{x3} IS NULL
        AND Cards.Copies > 0
        '''.format(synname=synname,groupColours=groupColours,groupRole=groupRole,p1=p1,p2=p2,x1=x1,x2=x2,x3=x3)
        for cardTuple in cursor2.execute(query2): # Execute with cursor2 to not lose place in outer loop
            synergiesLines.append("card;" + synergyLine +";"+ memberGroupLine +";"+ stringifyTuple(cardTuple))

# Print the FULL FINDINGS
print("recordType;SynergyColour;synergy;Payoffs;Participants;Score;GroupColour;GroupRole;GroupSize;Card;Colour")
for line in synergiesLines:
    print(line)

sys.exit()

################################ REPORTS #############################
# Search for only the 1 top synergy of each pair and list only those
unfound = colourPairs

topSynergies = []

print("Top synergy for each colour pair:")
while len(unfound) > 0:
    match = next((s for s in synergies if tuple(s[0]) in unfound), None)
    topSynergies.append(match)
    #print("Still unfound = ",unfound)
    unfound.remove(tuple(match[0]))
    
# Do the same reverse engineering on only the top synergies this time
for syn in topSynergies:
    print("Synergy is",syn)
    synname = syn[1]
    (p1,p2)=tuple(syn[0])
    (x1,x2,x3)=invertColourTuple((p1,p2))
    # Get summaries of the synergy member groups
    query = '''SELECT 
            --Synergies.Card, 
            Colour, 
            RolePlayed,
            COUNT(Synergies.Card) as cards
        FROM Synergies
        INNER JOIN Cards on Cards.Card=Synergies.Card
        WHERE Synergies.Synergy='{synname}'
        --AND (Cards.{p1} = 1 OR Cards.{p2} = 1) 
        AND Cards.{x1} IS NULL AND Cards.{x2} IS NULL AND Cards.{x3} IS NULL
        AND Cards.Copies > 0
        GROUP BY Colour, RolePlayed
        ORDER BY Colour       
        '''.format(synname=synname,p1=p1,p2=p2,x1=x1,x2=x2,x3=x3)

    # List the cards in the member groups
    for resultTuple in cursor.execute(query):
        print(" Synergy member group is ",resultTuple)
        groupColours = resultTuple[0]
        groupRole = resultTuple[1]
        
        query2 = '''SELECT 
            Synergies.Card, 
            Colour
        FROM Synergies
        INNER JOIN Cards on Cards.Card=Synergies.Card
        WHERE Synergies.Synergy='{synname}'
        AND Cards.Colour = '{groupColours}'
        AND Synergies.RolePlayed = '{groupRole}'
        --AND (Cards.{p1} = 1 OR Cards.{p2} = 1) 
        AND Cards.{x1} IS NULL AND Cards.{x2} IS NULL AND Cards.{x3} IS NULL
        AND Cards.Copies > 0
        '''.format(synname=synname,groupColours=groupColours,groupRole=groupRole,p1=p1,p2=p2,x1=x1,x2=x2,x3=x3)
        for card in cursor2.execute(query2): # Execute with cursor2 to not lose place in outer loop
            print("  ",card)
