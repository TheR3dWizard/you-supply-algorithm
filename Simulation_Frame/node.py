from .location import Location


class Node:
    def __init__(self, item:str,value:int,location:Location):
        self.item = item
        self.value = value
        self.location = location
        self.is_source = value > 0

    def get_distance(self,other) -> float:
        return self.location.get_distance(other.location)

    def s_copy(self):
        new_node = Node(self.item,self.value,self.location.copy())
        return new_node

    def change_value(self,new_value:int):
        self.value = new_value
        self.is_source = new_value > 0

    def split_sink(self,split_value:int):
        if split_value <= self.value:
            raise ValueError("Split value must be more than node value for sink")
        new_node = self.s_copy()
        new_node.change_value(split_value)
        self.change_value(self.value - split_value)
        return new_node

    def __str__(self):
        
        RESET = "\033[0m"
        BOLD = "\033[1m"

        CYAN = "\033[96m"
        GREEN = "\033[92m"
        YELLOW = "\033[93m"
        MAGENTA = "\033[95m"
        BLUE = "\033[94m"

        source_text = "Yes" if self.is_source else "No"
        source_color = GREEN if self.is_source else YELLOW

        return (
            f"\n{BOLD}{CYAN}Item:{RESET} {self.item}\n"
            f"{BOLD}{GREEN}Value:{RESET} {self.value}\n"
            f"{BOLD}{MAGENTA}Location:{RESET} {self.location}\n"
            f"{BOLD}{BLUE}Source:{RESET} {source_color}{source_text}{RESET}\n"
        )

    def __repr__(self):
        return (
            f"<Item:{self.item}, "
            f"Value:{self.value}, "
            f"Location:{self.location}, "
            f"Source:{self.is_source}>"
        )