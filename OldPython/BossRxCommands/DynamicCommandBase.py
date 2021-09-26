class DynamicCommandBase:

    def getValues(self):
        return []

    def matches(self, source):
        ret = None
        values = []
        if len(source) == len(self.base):
            test = source.copy()

            for i in self.maskIndices:
                test[i] = "*"

            test = "".join(test)
            if test == self.base:
                ret = self.name
                values = self.getValues(source)

        return ret, values