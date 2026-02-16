from collections import deque
from typing import Any, Deque, List, Optional, Dict, Tuple, Set
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, literal
from sqlalchemy.orm import selectinload, aliased
from app.models.germplasm import Germplasm, Cross
import uuid

class PedigreeService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _get_or_create_germplasm(self, name: str, organization_id: int) -> Germplasm:
        stmt = select(Germplasm).where(
            and_(
                Germplasm.organization_id == organization_id,
                or_(
                    Germplasm.germplasm_db_id == name,
                    Germplasm.germplasm_name == name
                )
            )
        )
        result = await self.db.execute(stmt)
        germplasm = result.scalar_one_or_none()

        if not germplasm:
            germplasm = Germplasm(
                germplasm_db_id=name, # Using name as db_id for simplicity if not exists
                germplasm_name=name,
                organization_id=organization_id,
                breeding_method_db_id="unknown"
            )
            self.db.add(germplasm)
            await self.db.flush() # flush to get ID

        return germplasm

    async def load_pedigree(self, pedigree_data: List[dict], organization_id: int = 1) -> dict:
        """
        Load a list of pedigree records (id, sire_id, dam_id) into the database.
        Returns statistics about the loaded data.
        """
        # 1. Ensure all individuals exist as Germplasm
        # We need to process topologically or just ensure all IDs are created first.
        # Let's create all mentions first.

        mentioned_ids = set()
        for record in pedigree_data:
            if record.get("id"): mentioned_ids.add(record["id"])
            if record.get("sire_id"): mentioned_ids.add(record["sire_id"])
            if record.get("dam_id"): mentioned_ids.add(record["dam_id"])

        germplasm_map = {} # name -> Germplasm object

        for name in mentioned_ids:
            germplasm_map[name] = await self._get_or_create_germplasm(name, organization_id)

        # 2. Create Crosses for individuals with parents
        processed_count = 0
        founders = 0

        for record in pedigree_data:
            child_name = record.get("id")
            sire_name = record.get("sire_id")
            dam_name = record.get("dam_id")

            if not child_name:
                continue

            child = germplasm_map[child_name]

            if not sire_name and not dam_name:
                founders += 1
                continue

            # Create or update Cross
            # Check if child already has a cross linked
            # For simplicity, we assume one cross per child in this context (pedigree tree)
            # In the model: Germplasm.cross_id -> Cross

            sire = germplasm_map.get(sire_name) if sire_name else None
            dam = germplasm_map.get(dam_name) if dam_name else None

            # Find existing cross?
            # We can create a new cross for this relationship

            cross_name = f"{sire_name or '?'}/{dam_name or '?'}"

            # Check if a cross with these parents already exists?
            # Or simpler: Check if child has a cross_id.

            if child.cross_id:
                # Already has parents. We might be updating.
                # Ideally we fetch the cross and update it.
                stmt = select(Cross).where(Cross.id == child.cross_id)
                result = await self.db.execute(stmt)
                cross = result.scalar_one_or_none()
                if cross:
                    cross.parent1_db_id = sire.id if sire else None
                    cross.parent2_db_id = dam.id if dam else None
            else:
                cross = Cross(
                    cross_db_id=str(uuid.uuid4()),
                    cross_name=cross_name,
                    cross_type="BIPARENTAL" if (sire and dam) else "UNKNOWN",
                    organization_id=organization_id,
                    parent1_db_id=sire.id if sire else None,
                    parent2_db_id=dam.id if dam else None
                )
                self.db.add(cross)
                await self.db.flush()

                child.cross_id = cross.id

            processed_count += 1

        await self.db.commit()

        stats = await self.get_stats(organization_id)
        return {
            "success": True,
            "message": f"Processed {processed_count} pedigree records",
            **stats
        }

    async def get_stats(self, organization_id: int = 1) -> dict:
        """
        Calculate pedigree statistics.
        """
        # Count individuals
        stmt_count = select(Germplasm).where(Germplasm.organization_id == organization_id)
        result_count = await self.db.execute(stmt_count)
        individuals = result_count.scalars().all()
        n_individuals = len(individuals)

        # Count founders (no cross_id or cross with no parents)
        # This is an approximation. A more accurate way is to check cross parents.
        # But efficiently:
        stmt_founders = select(Germplasm).where(
            and_(
                Germplasm.organization_id == organization_id,
                Germplasm.cross_id == None
            )
        )
        result_founders = await self.db.execute(stmt_founders)
        n_founders = len(result_founders.scalars().all())

        # Calculate generations and inbreeding is expensive for the whole DB.
        # We'll do a sample or basic check.
        # For now, return placeholders or cached stats if we had them.

        return {
            "n_individuals": n_individuals,
            "n_founders": n_founders,
            "n_generations": 0, # To be implemented properly
            "avg_inbreeding": 0,
            "max_inbreeding": 0,
            "completeness_index": 0
        }

    async def _calculate_generation(self, germplasm_id: int) -> int:
        """
        Calculates generation using a recursive CTE.
        Generation 0 = Founder (no recorded parents).
        Generation N = max(Generation(parents)) + 1
        """
        # Ancestry CTE
        # Base: The target individual, depth 0
        ancestry = select(
            Germplasm.id,
            literal(0).label('depth')
        ).where(Germplasm.id == germplasm_id).cte(name='ancestry', recursive=True)

        ancestry_alias = ancestry.alias("a")

        # Recursive: Join through Cross to Parents
        # Parents increase depth by 1

        child = aliased(Germplasm)
        parent = aliased(Germplasm)
        cr = aliased(Cross)

        recursive_part = select(
            parent.id,
            (ancestry_alias.c.depth + 1).label('depth')
        ).select_from(
            ancestry_alias
        ).join(
            child, child.id == ancestry_alias.c.id
        ).join(
            cr, cr.id == child.cross_id
        ).join(
            parent, or_(parent.id == cr.parent1_db_id, parent.id == cr.parent2_db_id)
        )

        ancestry = ancestry.union_all(recursive_part)

        # Select max depth
        stmt = select(func.max(ancestry.c.depth))
        result = await self.db.execute(stmt)
        max_depth = result.scalar()

        return max_depth if max_depth is not None else 0

    async def get_individual(self, individual_id: str, organization_id: int = 1) -> Optional[dict]:
        stmt = select(Germplasm).options(
            selectinload(Germplasm.cross).selectinload(Cross.parent1),
            selectinload(Germplasm.cross).selectinload(Cross.parent2)
        ).where(
            and_(
                Germplasm.organization_id == organization_id,
                or_(
                    Germplasm.germplasm_db_id == individual_id,
                    Germplasm.germplasm_name == individual_id
                )
            )
        )
        result = await self.db.execute(stmt)
        germplasm = result.scalar_one_or_none()

        if not germplasm:
            return None

        sire_id = None
        dam_id = None

        if germplasm.cross:
            if germplasm.cross.parent1:
                sire_id = germplasm.cross.parent1.germplasm_db_id
            if germplasm.cross.parent2:
                dam_id = germplasm.cross.parent2.germplasm_db_id

        generation = await self._calculate_generation(germplasm.id)

        return {
            "id": germplasm.germplasm_db_id,
            "sire_id": sire_id,
            "dam_id": dam_id,
            "generation": generation,
            "inbreeding": 0 # TODO: Calculate
        }

    async def get_individuals(self, generation: Optional[int] = None, page: int = 0, page_size: int = 1000, organization_id: int = 1) -> Tuple[List[dict], int]:
        # Fetch count
        count_stmt = select(Germplasm).where(Germplasm.organization_id == organization_id)
        # If generation filtering was implemented, we would add it here. Currently it is placeholder in model.

        count_res = await self.db.execute(count_stmt)
        total_count = len(count_res.scalars().all()) # Efficient count in SQL would be better: select(func.count())...

        # Fetch page
        stmt = select(Germplasm).options(
            selectinload(Germplasm.cross).selectinload(Cross.parent1),
            selectinload(Germplasm.cross).selectinload(Cross.parent2)
        ).where(Germplasm.organization_id == organization_id).limit(page_size).offset(page * page_size)

        result = await self.db.execute(stmt)
        germplasms = result.scalars().all()

        data = []
        for g in germplasms:
            sire_id = g.cross.parent1.germplasm_db_id if g.cross and g.cross.parent1 else None
            dam_id = g.cross.parent2.germplasm_db_id if g.cross and g.cross.parent2 else None

            data.append({
                "id": g.germplasm_db_id,
                "sire_id": sire_id,
                "dam_id": dam_id,
                "generation": 0,
                "inbreeding": 0
            })

        return data, total_count

    async def get_pedigree_graph(self, germplasm_id: str, depth: int = 2, organization_id: int = 1) -> Dict[str, List[Dict[str, Any]]]:
        """
        Build a pedigree graph around a central germplasm node and format it
        for Cytoscape ({"nodes": [], "edges": []}).
        """
        if depth < 0:
            depth = 0

        # Step 1: Fetch central node
        root_stmt = select(Germplasm).options(
            selectinload(Germplasm.cross).selectinload(Cross.parent1),
            selectinload(Germplasm.cross).selectinload(Cross.parent2),
        ).where(
            and_(
                Germplasm.organization_id == organization_id,
                or_(
                    Germplasm.germplasm_db_id == germplasm_id,
                    Germplasm.germplasm_name == germplasm_id,
                ),
            )
        )
        root_res = await self.db.execute(root_stmt)
        root = root_res.scalar_one_or_none()
        if not root:
            raise ValueError(f"Germplasm '{germplasm_id}' not found")

        node_map: Dict[str, Dict[str, Any]] = {}
        edge_set: Set[Tuple[str, str]] = set()

        def _node_id(g: Germplasm) -> str:
            return g.germplasm_db_id or g.germplasm_name or str(g.id)

        def _node_label(g: Germplasm) -> str:
            return g.germplasm_name or g.germplasm_db_id or str(g.id)

        def add_node(g: Optional[Germplasm]) -> Optional[str]:
            if not g:
                return None
            gid = _node_id(g)
            node_map[gid] = {"id": gid, "label": _node_label(g), "type": "germplasm"}
            return gid

        root_node_id = add_node(root)

        # Step 2: Fetch ancestors up to depth using iterative traversal
        visited_ancestors: Set[int] = set()
        ancestor_queue: Deque[Tuple[Germplasm, int]] = deque([(root, 0)])

        while ancestor_queue:
            current, curr_depth = ancestor_queue.popleft()
            if current.id in visited_ancestors:
                continue
            visited_ancestors.add(current.id)
            if curr_depth >= depth:
                continue

            if not current.cross:
                continue

            parents = [current.cross.parent1, current.cross.parent2]
            child_node_id = add_node(current)
            for parent in parents:
                if parent and parent.id == current.id:
                    raise RuntimeError("Circular pedigree dependency detected (self-parent)")
                parent_node_id = add_node(parent)
                if parent_node_id and child_node_id:
                    edge_set.add((parent_node_id, child_node_id))
                if parent and parent.id not in visited_ancestors:
                    ancestor_queue.append((parent, curr_depth + 1))

        # Step 3: Fetch descendants up to depth (forward links via Cross.progeny)
        visited_descendants: Set[int] = set()
        descendant_queue: Deque[Tuple[Germplasm, int]] = deque([(root, 0)])

        while descendant_queue:
            current, curr_depth = descendant_queue.popleft()
            if current.id in visited_descendants:
                continue
            visited_descendants.add(current.id)
            if curr_depth >= depth:
                continue

            child_stmt = select(Germplasm).options(
                selectinload(Germplasm.cross).selectinload(Cross.parent1),
                selectinload(Germplasm.cross).selectinload(Cross.parent2),
            ).join(Cross, Germplasm.cross_id == Cross.id).where(
                and_(
                    Germplasm.organization_id == organization_id,
                    or_(
                        Cross.parent1_db_id == current.id,
                        Cross.parent2_db_id == current.id,
                    ),
                )
            )
            child_res = await self.db.execute(child_stmt)
            children = child_res.scalars().all()

            for child in children:
                child_node_id = add_node(child)
                if child_node_id:
                    if child.cross and child.cross.parent1:
                        if child.cross.parent1.id == child.id:
                            raise RuntimeError("Circular pedigree dependency detected (self-parent)")
                        edge_set.add((_node_id(child.cross.parent1), child_node_id))
                    if child.cross and child.cross.parent2:
                        if child.cross.parent2.id == child.id:
                            raise RuntimeError("Circular pedigree dependency detected (self-parent)")
                        edge_set.add((_node_id(child.cross.parent2), child_node_id))
                if child.id not in visited_descendants:
                    descendant_queue.append((child, curr_depth + 1))

        if not root_node_id:
            raise ValueError(f"Unable to build graph for germplasm '{germplasm_id}'")

        # Step 4: Format for Cytoscape
        return {
            "nodes": [{"data": node} for node in node_map.values()],
            "edges": [
                {"data": {"source": source, "target": target}}
                for source, target in sorted(edge_set)
            ],
        }

    async def get_ancestors(self, individual_id: str, max_generations: int = 5, organization_id: int = 1) -> dict:
        """
        Trace ancestors using Recursive CTE for efficient retrieval.
        Relation: Germplasm (Child) -> Cross -> Germplasm (Parent)
        """
        from sqlalchemy import literal, union_all
        from sqlalchemy.orm import aliased

        # 1. Get database ID of the starting individual
        stmt = select(Germplasm.id, Germplasm.cross_id).where(
            and_(
                Germplasm.organization_id == organization_id,
                Germplasm.germplasm_db_id == individual_id
            )
        )
        result = await self.db.execute(stmt)
        start_node = result.first() # (id, cross_id)

        if not start_node:
            return {"error": f"Individual {individual_id} not found", "ancestors": []}

        start_id, start_cross_id = start_node

        # 2. Define Recursive CTE
        # We need to traverse UP data: Child -> Parent

        # Base case: The starting individual
        # We select: id, cross_id, generation, path (for tracking)
        hierarchy = select(
            Germplasm.id,
            Germplasm.germplasm_db_id,
            Germplasm.germplasm_name,
            Germplasm.cross_id,
            literal(0).label('generation')
        ).where(Germplasm.id == start_id).cte(name="ancestral_tree", recursive=True)

        # Recursive part: Find parents of individuals in the hierarchy
        # Logic:
        # Current (Child) has cross_id.
        # Cross table has parent1_db_id and parent2_db_id pointing to Parent Germplasm.id

        parent_germplasm = aliased(Germplasm)
        c = aliased(Cross)

        recursive_stmt = select(
            parent_germplasm.id,
            parent_germplasm.germplasm_db_id,
            parent_germplasm.germplasm_name,
            parent_germplasm.cross_id,
            (hierarchy.c.generation + 1).label('generation')
        ).select_from(hierarchy).join(
            c, c.id == hierarchy.c.cross_id
        ).join(
            parent_germplasm,
            or_(
                parent_germplasm.id == c.parent1_db_id,
                parent_germplasm.id == c.parent2_db_id
            )
        ).where(hierarchy.c.generation < max_generations)

        # Combine
        combined_cte = hierarchy.union_all(recursive_stmt)

        # 3. Execute CTE
        final_stmt = select(combined_cte)
        res = await self.db.execute(final_stmt)
        rows = res.all()

        # 4. Format Output
        # To build a tree, we need the relationships.
        # The CTE gives us the nodes. We need to know the edges (parents) for each node to reconstruct the tree.
        # We can fetch all these individuals and their parents.

        ancestor_db_ids = [row.germplasm_db_id for row in rows]
        if individual_id not in ancestor_db_ids:
            ancestor_db_ids.append(individual_id)

        # Fetch detailed info for all involved individuals (to get sire/dam)
        # We can reuse get_individual or just query in bulk
        stmt_details = select(Germplasm).options(
            selectinload(Germplasm.cross).selectinload(Cross.parent1),
            selectinload(Germplasm.cross).selectinload(Cross.parent2)
        ).where(
            and_(
                Germplasm.organization_id == organization_id,
                Germplasm.germplasm_db_id.in_(ancestor_db_ids)
            )
        )
        res_details = await self.db.execute(stmt_details)
        details_map = {g.germplasm_db_id: g for g in res_details.scalars().all()}

        # Build Tree Function
        def build_tree(curr_id: str, current_depth: int) -> Optional[Dict]:
            if current_depth > max_generations:
                return None

            g = details_map.get(curr_id)
            if not g:
                return None

            node = {
                "id": g.germplasm_db_id,
                "name": g.germplasm_name,
                "generation": current_depth, # Relative to start
                "type": "germplasm" # Frontend expects this
            }

            # Find parents
            sire_id = None
            dam_id = None
            if g.cross:
                if g.cross.parent1: sire_id = g.cross.parent1.germplasm_db_id
                if g.cross.parent2: dam_id = g.cross.parent2.germplasm_db_id

            if sire_id:
                node["parent1"] = build_tree(sire_id, current_depth + 1)
            if dam_id:
                node["parent2"] = build_tree(dam_id, current_depth + 1)

            return node

        tree_root = build_tree(individual_id, 0)

        ancestors_set = set(ancestor_db_ids)
        if individual_id in ancestors_set:
            ancestors_set.remove(individual_id)

        return {
            "individual_id": individual_id,
            "n_ancestors": len(ancestors_set),
            "ancestors": list(ancestors_set),
            "tree": tree_root, # Nested structure
            # "tree_flat": tree_nodes # Optional: keep if helpful debugging
        }

    async def get_descendants(self, individual_id: str, max_generations: int = 3, organization_id: int = 1) -> dict:
        # This is harder without a parent->child index.
        # We need to find all crosses where parent1 or parent2 is the individual.

        descendants_set = set()

        async def fetch_children(curr_id, depth):
            if depth >= max_generations:
                return

            # Find germplasm ID
            stmt_g = select(Germplasm.id).where(
                and_(
                    Germplasm.organization_id == organization_id,
                    Germplasm.germplasm_db_id == curr_id
                )
            )
            res_g = await self.db.execute(stmt_g)
            g_id = res_g.scalar_one_or_none()

            if not g_id:
                return

            # Find crosses where this germplasm is a parent
            stmt_c = select(Cross.id).where(
                or_(
                    Cross.parent1_db_id == g_id,
                    Cross.parent2_db_id == g_id
                )
            )
            res_c = await self.db.execute(stmt_c)
            cross_ids = res_c.scalars().all()

            if not cross_ids:
                return

            # Find germplasms from these crosses
            stmt_kids = select(Germplasm).where(Germplasm.cross_id.in_(cross_ids))
            res_kids = await self.db.execute(stmt_kids)
            kids = res_kids.scalars().all()

            for kid in kids:
                if kid.germplasm_db_id not in descendants_set:
                    descendants_set.add(kid.germplasm_db_id)
                    await fetch_children(kid.germplasm_db_id, depth + 1)

        await fetch_children(individual_id, 0)

        return {
            "individual_id": individual_id,
            "n_descendants": len(descendants_set),
            "descendants": list(descendants_set)
        }

    async def calculate_coancestry(self, id1: str, id2: str, organization_id: int = 1) -> dict:
        # Placeholder for complex calculation
        # If same individual, 0.5 (or 0.5 + F/2)
        # If parent-child, 0.25
        # If full sibs, 0.25

        if id1 == id2:
            return {
                "individual_1": id1,
                "individual_2": id2,
                "coancestry": 0.5,
                "relationship": "Same individual"
            }

        # Get immediate parents
        ind1 = await self.get_individual(id1, organization_id)
        ind2 = await self.get_individual(id2, organization_id)

        if not ind1 or not ind2:
             return {
                "individual_1": id1,
                "individual_2": id2,
                "coancestry": 0.0,
                "relationship": "Unknown"
            }

        # Basic check for Parent-Child
        is_parent_child = (
            ind1["sire_id"] == id2 or ind1["dam_id"] == id2 or
            ind2["sire_id"] == id1 or ind2["dam_id"] == id1
        )

        if is_parent_child:
             return {
                "individual_1": id1,
                "individual_2": id2,
                "coancestry": 0.25,
                "relationship": "Parent-Offspring"
            }

        # Basic check for Full Siblings
        is_full_sibs = (
            ind1["sire_id"] and ind1["dam_id"] and
            ind1["sire_id"] == ind2["sire_id"] and
            ind1["dam_id"] == ind2["dam_id"]
        )

        if is_full_sibs:
            return {
                "individual_1": id1,
                "individual_2": id2,
                "coancestry": 0.25,
                "relationship": "Full Siblings"
            }

        return {
            "individual_1": id1,
            "individual_2": id2,
            "coancestry": 0.0,
            "relationship": "Unrelated (or calculation too complex)"
        }
