import sqlite3
import itertools
import sys # Useful to have for sys.exit()

def invertColourTuple(colourTuple):
	inverse = ["W","U","B","R","G"]
	for c in colourTuple:
		#print("Removing", c ,"from", inverse)
		inverse.remove(c)
	return inverse


connection = sqlite3.connect('cubedb.sqlite')
cursor = connection.cursor()

colours = ["W","U","B","R","G"]
shardsAndWedges = list(itertools.combinations(colours, r=3))
print(shardsAndWedges)
colourPairs = list(itertools.combinations(colours, r=2))
synergies = []

for c1, c2, c3 in shardsAndWedges:

	query = '''SELECT
		'{c1}{c2}{c3}',
		Synergies.Synergy,
		COUNT(CASE WHEN Synergies.RolePlayed='Payoff' THEN 1 END) as Payoffs, 
		COUNT(CASE WHEN Synergies.RolePlayed='Participant' THEN 1 END) as Participants,
		(COUNT(CASE WHEN Synergies.RolePlayed='Payoff' THEN 1 END) * COUNT(CASE WHEN Synergies.RolePlayed='Participant' THEN 1 END)) as Product 
	FROM Synergies
	INNER JOIN Cards ON Cards.Card=Synergies.Card
	WHERE (Cards.{c1} IS NULL AND Cards.{c2} IS NULL AND Cards.{c3} IS NULL)
	GROUP BY Synergies.Synergy
	ORDER BY (COUNT(CASE WHEN Synergies.RolePlayed='Payoff' THEN 1 END) * COUNT(CASE WHEN Synergies.RolePlayed='Participant' THEN 1 END)) DESC;'''.format(c1=c1,c2=c2,c3=c3)

	for synergyTuple in cursor.execute(query):
		if (synergyTuple[4] > 0):
			synergies.append((''.join(invertColourTuple(tuple(synergyTuple[0]))), synergyTuple[1], synergyTuple[2], synergyTuple[3], synergyTuple[4]))

def synergyScore(synergyTuple):
	return synergyTuple[4]

synergies.sort(key=synergyScore,reverse=False)

for s in synergies:
	print(s)

# Sort (for ease of log-browsing)
synergies.sort(key=synergyScore,reverse=True)
	
print("Top results for each")
	
unfound = colourPairs

print(unfound)

while len(unfound) > 0:
	match = next((s for s in synergies if tuple(s[0]) in unfound), None)
	print(match)
	unfound.remove(tuple(match[0]))
	

	
