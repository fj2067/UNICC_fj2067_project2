class SafetyCouncil:

    def __init__(self, judges):
        self.judges = judges

    def evaluate(self, text):

        results = []

        for judge in self.judges:
            result = judge.evaluate(text)
            results.append(result)

        return results
