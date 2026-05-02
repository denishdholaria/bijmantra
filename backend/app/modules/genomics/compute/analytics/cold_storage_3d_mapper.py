from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict

class StorageUnitType(str, Enum):
    WAREHOUSE = "warehouse"
    ROOM = "room"
    AISLE = "aisle"
    RACK = "rack"
    SHELF = "shelf"
    BOX = "box"
    CELL = "cell"

class Coordinates(BaseModel):
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0

class Dimensions(BaseModel):
    width: float = 0.0
    height: float = 0.0
    depth: float = 0.0

class StorageNode(BaseModel):
    id: str
    code: str
    type: StorageUnitType
    dimensions: Optional[Dimensions] = None
    local_coordinates: Optional[Coordinates] = None # Relative to parent
    global_coordinates: Optional[Coordinates] = None # Absolute world coordinates
    children: List['StorageNode'] = Field(default_factory=list)
    parent_id: Optional[str] = None
    metadata: Dict = Field(default_factory=dict)

    model_config = ConfigDict(arbitrary_types_allowed=True)

class ColdStorage3DMapper:
    """
    Maps logical inventory locations to 3D spatial coordinates.
    """
    def __init__(self, config: Dict):
        """
        Initialize with configuration defining dimensions and layout rules.

        Example config:
        {
            "warehouse": {"width": 1000, "height": 500, "depth": 1000},
            "rack": {"width": 100, "height": 200, "depth": 50, "shelves": 5},
            "shelf": {"height": 40},
            "box": {"width": 20, "height": 15, "depth": 30},
            "aisle_width": 150,
            "rack_spacing": 20
        }
        """
        self.config = config

    def parse_location_code(self, code: str) -> List[Dict[str, str]]:
        """
        Parses a location code like 'WH1-R2-S3-B4' into a hierarchy components.
        Returns a list of dicts: [{'type': 'warehouse', 'id': 'WH1', 'index': 1}, ...]
        Assumes standard format: {TypePrefix}{Index}-...
        Prefixes: WH=Warehouse, R=Rack, S=Shelf, B=Box
        """
        parts = code.split('-')
        hierarchy = []
        for part in parts:
            item = {}
            if part.startswith('WH'):
                item = {'type': StorageUnitType.WAREHOUSE, 'id': part, 'prefix': 'WH'}
            elif part.startswith('R'):
                item = {'type': StorageUnitType.RACK, 'id': part, 'prefix': 'R'}
            elif part.startswith('S'):
                item = {'type': StorageUnitType.SHELF, 'id': part, 'prefix': 'S'}
            elif part.startswith('B'):
                item = {'type': StorageUnitType.BOX, 'id': part, 'prefix': 'B'}
            else:
                # Fallback or unknown
                continue

            # Extract index
            try:
                index_str = part.replace(item['prefix'], '')
                if index_str.isdigit():
                    item['index'] = int(index_str)
                else:
                    item['index'] = 0 # Default if non-numeric
            except Exception:
                item['index'] = 0

            hierarchy.append(item)
        return hierarchy

    def get_dimensions(self, unit_type: StorageUnitType) -> Dimensions:
        """Get dimensions from config for a specific type"""
        cfg = self.config.get(unit_type.value, {})
        return Dimensions(
            width=cfg.get('width', 0),
            height=cfg.get('height', 0),
            depth=cfg.get('depth', 0)
        )

    def calculate_local_coordinates(self, node_type: StorageUnitType, index: int, parent_type: Optional[StorageUnitType]) -> Coordinates:
        """
        Calculate local coordinates relative to parent based on index and type.
        This is a simplified grid layout logic.
        """
        coords = Coordinates()

        if node_type == StorageUnitType.RACK:
            # Assume racks are lined up along X axis with aisle spacing
            # Simple row logic: Rack 1 at 0, Rack 2 at width + spacing...
            rack_width = self.config.get('rack', {}).get('width', 100)
            rack_spacing = self.config.get('rack_spacing', 20)
            coords.x = (index - 1) * (rack_width + rack_spacing)
            coords.y = 0 # On the floor
            coords.z = 0 # Simple 1D row

        elif node_type == StorageUnitType.SHELF:
            # Shelves stacked vertically (Y axis)
            shelf_height = self.config.get('shelf', {}).get('height', 40)
            # Assuming shelf 1 is at bottom
            coords.x = 0
            coords.y = (index - 1) * shelf_height
            coords.z = 0

        elif node_type == StorageUnitType.BOX:
            # Boxes on a shelf, arranged along X then Z?
            # Simple assumption: Boxes arranged along X
            box_width = self.config.get('box', {}).get('width', 20)
            coords.x = (index - 1) * box_width
            coords.y = 0 # On the shelf surface
            coords.z = 0

        return coords

    def build_node(self, type_info: Dict, parent: Optional[StorageNode] = None) -> StorageNode:
        """Construct a single node"""
        unit_type = type_info['type']
        dims = self.get_dimensions(unit_type)

        index = type_info.get('index', 1)
        parent_type = parent.type if parent else None

        local_coords = self.calculate_local_coordinates(unit_type, index, parent_type)

        # Calculate global
        if parent and parent.global_coordinates:
            global_coords = Coordinates(
                x=parent.global_coordinates.x + local_coords.x,
                y=parent.global_coordinates.y + local_coords.y,
                z=parent.global_coordinates.z + local_coords.z
            )
        else:
            global_coords = local_coords

        return StorageNode(
            id=type_info['id'],
            code=type_info['id'],
            type=unit_type,
            dimensions=dims,
            local_coordinates=local_coords,
            global_coordinates=global_coords,
            parent_id=parent.id if parent else None
        )

    def process_location(self, code: str) -> StorageNode:
        """
        Process a single location code into a linked list of nodes (path).
        Returns the leaf node (e.g. Box), with parent references populated.
        Note: This returns a distinct path. Merging into a full tree requires a separate step.
        """
        hierarchy = self.parse_location_code(code)
        parent = None
        leaf = None

        for item in hierarchy:
            node = self.build_node(item, parent)
            if parent:
                # We don't add to parent.children here because we are just building the path for this specific location
                # In a full tree builder, we would check if node exists in parent's children
                pass
            parent = node
            leaf = node

        return leaf

    def build_full_hierarchy(self, codes: List[str]) -> StorageNode:
        """
        Takes a list of location codes and builds a complete tree.
        Assumes a single root warehouse for simplicity or wraps in a virtual root.
        """
        root = StorageNode(
            id="ROOT",
            code="ROOT",
            type=StorageUnitType.WAREHOUSE,
            dimensions=self.get_dimensions(StorageUnitType.WAREHOUSE),
            global_coordinates=Coordinates(x=0,y=0,z=0)
        )

        # Helper to find child by ID
        def find_child(node: StorageNode, child_id: str) -> Optional[StorageNode]:
            for child in node.children:
                if child.id == child_id:
                    return child
            return None

        for code in codes:
            parts = self.parse_location_code(code)
            current_node = root

            for part in parts:
                existing_node = find_child(current_node, part['id'])
                if existing_node:
                    current_node = existing_node
                else:
                    new_node = self.build_node(part, current_node)
                    current_node.children.append(new_node)
                    current_node = new_node

        return root
