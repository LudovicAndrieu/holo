from holo.__typing import Literal, Iterable, DefaultDict, Generic, TypeVar

_GameResult = Literal["win", "lose", "draw", True, False, None]
"""win == True | lose == False | draw == None"""

_T_Datas = TypeVar("_T_Datas")
class Player(Generic[_T_Datas]):
    __slots__ = ("name", "elo", "datas")
    
    def __init__(self, name:str, defaultElo:float=1000, 
                 datas:_T_Datas=None) -> None:
        self.name: str = name
        self.elo: float = defaultElo
        self.datas: _T_Datas = datas

    def expectedWinRate(self, opponent:"Player")->float:
        return 1 / (1 + 10 ** ((opponent.elo - self.elo)/400))
    
    def __str__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name}, elo={self.elo:.6g})"



class Ranking():
    __slots__ = ("players", "k", "delfautElo", )
    __ConvertGameResult: "dict[_GameResult, float]" = {
        "win": 1.0, "lose": 0.0, "draw": 0.5,
        True: 1.0, False: 0.0, None: 0.5}
    
    def __init__(
            self, players:"Iterable[Player|str]|None"=None, 
            k:float=32, delfautElo:float=1000.0) -> None:
        self.k: float = k
        self.delfautElo: float = delfautElo
        self.players: "dict[str, Player]" = {}
        if players is not None:
            self.addPlayers(players)
    
    def addPlayers(self, players:"Iterable[Player|str]")->"list[Player]":
        newPlayers: "dict[str, Player]" = {}
        for player in players:
            if isinstance(player, Player):
                name = player.name
            else:  
                name = player
                player = Player(name=name, defaultElo=self.delfautElo)
            if name in self.players:
                raise ValueError(f"the player: {name!r} alredy exist")
            if name in newPlayers:
                raise ValueError(f"trying to add the player: {name!r} twice")
            newPlayers[name] = player
        # => all players can be added
        self.players.update(newPlayers)
        return list(newPlayers.values())
    
    def upddate(self, player:Player, opponent:Player, result:_GameResult)->None:
        """update the elo of both players after 1 game\n
        allow players to not be registerd with this system"""
        actualScore: float = self.__ConvertGameResult[result]
        expectedScore: float = player.expectedWinRate(opponent)
        deltaEloPlayer = self.k * (actualScore - expectedScore)
        deltaEloOpponent = self.k * (expectedScore - actualScore)
        player.elo += deltaEloPlayer
        opponent.elo += deltaEloOpponent
    
    def updateMultiple(self, results:"Iterable[tuple[Player, Player, _GameResult]]")->None:
        """update the elo of all players after multiple game\n
        this has a different result than doin one update at the time\n
        match don't need to be duplicated, results are applied to both\n
        allow players to not be registerd with this system"""
        playersActualScores: dict[Player, float] = DefaultDict(float)
        playersExpectedScores: dict[Player, float] = DefaultDict(float)
        for player, opponent, result in results:
            score = self.__ConvertGameResult[result]
            playersActualScores[player] += score
            playersActualScores[opponent] += (1-score)
            expectedScore = player.expectedWinRate(opponent)
            playersExpectedScores[player] += expectedScore
            playersExpectedScores[opponent] += (1-expectedScore)
        for player, actualScore in playersActualScores.items():
            expectedScore = playersExpectedScores[player]
            player.elo += self.k * (actualScore - expectedScore)
            