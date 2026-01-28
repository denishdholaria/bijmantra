"""
Demo Genotyping Seeder
Seeds genotyping data (references, variants, calls, maps) into Demo Organization
"""

import uuid
from sqlalchemy import select
from app.db.seeders.base import BaseSeeder, register_seeder
from app.models.core import Organization
from app.models.genotyping import (
    ReferenceSet, Reference, GenomeMap, LinkageGroup, MarkerPosition,
    VariantSet, Variant, CallSet, Call, Plate, VendorOrder
)
import logging

logger = logging.getLogger(__name__)


@register_seeder
class DemoGenotypingSeeder(BaseSeeder):
    """Seeds demo genotyping data for development/testing"""
    
    name = "demo_genotyping"
    description = "Demo genotyping data (references, variants, calls, maps)"
    
    def seed(self) -> int:
        """Seed demo genotyping data"""
        from app.core.config import settings
        
        # Get demo organization
        demo_org = self.db.execute(
            select(Organization).where(Organization.name == settings.DEMO_ORG_NAME)
        ).scalar_one_or_none()
        
        if not demo_org:
            logger.warning("Demo Organization not found. Run demo_users seeder first.")
            return 0
        
        org_id = demo_org.id
        total = 0
        
        # Check if already seeded
        existing = self.db.execute(
            select(ReferenceSet).where(ReferenceSet.organization_id == org_id).limit(1)
        ).scalar_one_or_none()
        
        if existing:
            logger.info("Genotyping data already seeded")
            return 0
        
        # Seed reference sets and references
        total += self._seed_reference_sets(org_id)
        
        # Seed genome maps
        total += self._seed_genome_maps(org_id)
        
        # Seed variant sets and variants
        total += self._seed_variant_sets(org_id)
        
        # Seed call sets and calls
        total += self._seed_call_sets(org_id)
        
        # Seed plates
        total += self._seed_plates(org_id)
        
        # Seed vendor orders
        total += self._seed_vendor_orders(org_id)
        
        self.db.commit()
        logger.info(f"Seeded {total} genotyping records")
        return total
    
    def _seed_reference_sets(self, org_id: int) -> int:
        """Seed reference sets and references"""
        count = 0
        
        reference_sets_data = [
            {
                "reference_set_db_id": f"refset_rice_{uuid.uuid4().hex[:8]}",
                "reference_set_name": "IRGSP-1.0",
                "description": "International Rice Genome Sequencing Project Reference",
                "assembly_pui": "GCF_001433935.1",
                "references": [
                    {"name": "Chr1", "length": 43270923},
                    {"name": "Chr2", "length": 35937250},
                    {"name": "Chr3", "length": 36413819},
                    {"name": "Chr4", "length": 35502694},
                    {"name": "Chr5", "length": 29958434},
                    {"name": "Chr6", "length": 31248787},
                ]
            },
            {
                "reference_set_db_id": f"refset_wheat_{uuid.uuid4().hex[:8]}",
                "reference_set_name": "IWGSC RefSeq v2.1",
                "description": "International Wheat Genome Sequencing Consortium Reference",
                "assembly_pui": "GCF_018294505.1",
                "references": [
                    {"name": "1A", "length": 594102056},
                    {"name": "1B", "length": 689851870},
                    {"name": "1D", "length": 495453186},
                ]
            },
        ]
        
        for rs_data in reference_sets_data:
            refs = rs_data.pop("references", [])
            ref_set = ReferenceSet(organization_id=org_id, **rs_data)
            self.db.add(ref_set)
            self.db.flush()
            count += 1
            
            for ref_data in refs:
                ref = Reference(
                    organization_id=org_id,
                    reference_set_id=ref_set.id,
                    reference_db_id=f"ref_{ref_data['name'].lower()}_{uuid.uuid4().hex[:8]}",
                    reference_name=ref_data["name"],
                    length=ref_data["length"]
                )
                self.db.add(ref)
                count += 1
        
        logger.info(f"Seeded {count} reference sets and references")
        return count
    
    def _seed_genome_maps(self, org_id: int) -> int:
        """Seed genome maps with linkage groups"""
        count = 0
        
        maps_data = [
            {
                "map_db_id": f"map_rice_{uuid.uuid4().hex[:8]}",
                "map_name": "Rice High-Density SNP Map",
                "common_crop_name": "Rice",
                "type": "genetic",
                "unit": "cM",
                "linkage_groups": [
                    {"name": "Chr1", "max_position": 180.5},
                    {"name": "Chr2", "max_position": 165.2},
                    {"name": "Chr3", "max_position": 172.8},
                ]
            },
        ]
        
        for map_data in maps_data:
            lgs = map_data.pop("linkage_groups", [])
            genome_map = GenomeMap(organization_id=org_id, **map_data)
            self.db.add(genome_map)
            self.db.flush()
            count += 1
            
            for lg_data in lgs:
                lg = LinkageGroup(
                    organization_id=org_id,
                    map_id=genome_map.id,
                    linkage_group_name=lg_data["name"],
                    max_position=lg_data["max_position"]
                )
                self.db.add(lg)
                count += 1
        
        logger.info(f"Seeded {count} genome maps and linkage groups")
        return count
    
    def _seed_variant_sets(self, org_id: int) -> int:
        """Seed variant sets and variants"""
        count = 0
        
        # Get first reference set
        ref_set = self.db.execute(
            select(ReferenceSet).where(ReferenceSet.organization_id == org_id).limit(1)
        ).scalar_one_or_none()
        
        # Get first reference
        ref = self.db.execute(
            select(Reference).where(Reference.organization_id == org_id).limit(1)
        ).scalar_one_or_none()
        
        variant_set = VariantSet(
            organization_id=org_id,
            variant_set_db_id=f"vs_rice_{uuid.uuid4().hex[:8]}",
            variant_set_name="Rice 3K SNP Dataset",
            reference_set_id=ref_set.id if ref_set else None,
            call_set_count=4,
            variant_count=5
        )
        self.db.add(variant_set)
        self.db.flush()
        count += 1
        
        # Add variants
        variants_data = [
            {"name": "SNP_1_1000", "type": "SNP", "ref": "A", "alt": "G", "start": 1000},
            {"name": "SNP_1_5000", "type": "SNP", "ref": "C", "alt": "T", "start": 5000},
            {"name": "SNP_1_10000", "type": "SNP", "ref": "G", "alt": "A", "start": 10000},
            {"name": "INDEL_1_15000", "type": "INDEL", "ref": "AT", "alt": "A", "start": 15000},
            {"name": "SNP_1_20000", "type": "SNP", "ref": "T", "alt": "C", "start": 20000},
        ]
        
        for var_data in variants_data:
            variant = Variant(
                organization_id=org_id,
                variant_set_id=variant_set.id,
                reference_id=ref.id if ref else None,
                variant_db_id=f"var_{uuid.uuid4().hex[:8]}",
                variant_name=var_data["name"],
                variant_type=var_data["type"],
                reference_bases=var_data["ref"],
                alternate_bases=[var_data["alt"]],
                start=var_data["start"],
                end=var_data["start"] + len(var_data["ref"])
            )
            self.db.add(variant)
            count += 1
        
        logger.info(f"Seeded {count} variant sets and variants")
        return count
    
    def _seed_call_sets(self, org_id: int) -> int:
        """Seed call sets and calls"""
        count = 0
        
        # Get variant set
        variant_set = self.db.execute(
            select(VariantSet).where(VariantSet.organization_id == org_id).limit(1)
        ).scalar_one_or_none()
        
        if not variant_set:
            return 0
        
        # Get variants
        variants = self.db.execute(
            select(Variant).where(Variant.variant_set_id == variant_set.id)
        ).scalars().all()
        
        call_sets_data = [
            {"name": "IR64", "sample": "sample-ir64"},
            {"name": "Nipponbare", "sample": "sample-nipponbare"},
            {"name": "Kasalath", "sample": "sample-kasalath"},
            {"name": "N22", "sample": "sample-n22"},
        ]
        
        genotypes = [
            ["0/0", "0/1", "1/1", "0/0", "0/1"],
            ["0/0", "0/0", "0/1", "1/1", "0/0"],
            ["1/1", "0/1", "0/0", "0/1", "1/1"],
            ["0/1", "1/1", "0/1", "0/0", "0/1"],
        ]
        
        for i, cs_data in enumerate(call_sets_data):
            call_set = CallSet(
                organization_id=org_id,
                call_set_db_id=f"cs_{cs_data['name'].lower()}_{uuid.uuid4().hex[:8]}",
                call_set_name=cs_data["name"],
                sample_db_id=cs_data["sample"]
            )
            self.db.add(call_set)
            self.db.flush()
            count += 1
            
            # Add calls for each variant
            for j, variant in enumerate(variants):
                gt = genotypes[i][j] if j < len(genotypes[i]) else "0/0"
                call = Call(
                    organization_id=org_id,
                    variant_id=variant.id,
                    call_set_id=call_set.id,
                    call_db_id=f"call_{uuid.uuid4().hex[:8]}",
                    genotype_value=gt,
                    genotype={"values": gt.split("/")}
                )
                self.db.add(call)
                count += 1
        
        logger.info(f"Seeded {count} call sets and calls")
        return count
    
    def _seed_plates(self, org_id: int) -> int:
        """Seed plates"""
        count = 0
        
        plates_data = [
            {"name": "Rice_Diversity_Plate_1", "barcode": "RDP001", "format": "PLATE_96"},
            {"name": "Rice_Diversity_Plate_2", "barcode": "RDP002", "format": "PLATE_96"},
            {"name": "Wheat_GWAS_Plate_1", "barcode": "WGP001", "format": "PLATE_384"},
        ]
        
        for plate_data in plates_data:
            plate = Plate(
                organization_id=org_id,
                plate_db_id=f"plate_{uuid.uuid4().hex[:8]}",
                plate_name=plate_data["name"],
                plate_barcode=plate_data["barcode"],
                plate_format=plate_data["format"],
                sample_type="DNA"
            )
            self.db.add(plate)
            count += 1
        
        logger.info(f"Seeded {count} plates")
        return count
    
    def _seed_vendor_orders(self, org_id: int) -> int:
        """Seed vendor orders"""
        count = 0
        
        orders_data = [
            {"order_id": "ORD-2024-001", "samples": 96, "status": "COMPLETED"},
            {"order_id": "ORD-2024-002", "samples": 384, "status": "INPROGRESS"},
            {"order_id": "ORD-2024-003", "samples": 48, "status": "REGISTERED"},
        ]
        
        for order_data in orders_data:
            order = VendorOrder(
                organization_id=org_id,
                order_db_id=f"order_{uuid.uuid4().hex[:8]}",
                client_id="client-bijmantra",
                order_id=order_data["order_id"],
                number_of_samples=order_data["samples"],
                status=order_data["status"]
            )
            self.db.add(order)
            count += 1
        
        logger.info(f"Seeded {count} vendor orders")
        return count
    
    def clear(self) -> int:
        """Clear demo genotyping data"""
        from app.core.config import settings
        
        demo_org = self.db.execute(
            select(Organization).where(Organization.name == settings.DEMO_ORG_NAME)
        ).scalar_one_or_none()
        
        if not demo_org:
            return 0
        
        total = 0
        org_id = demo_org.id
        
        # Delete in reverse order of dependencies
        total += self.db.query(Call).filter(Call.organization_id == org_id).delete()
        total += self.db.query(CallSet).filter(CallSet.organization_id == org_id).delete()
        total += self.db.query(Variant).filter(Variant.organization_id == org_id).delete()
        total += self.db.query(VariantSet).filter(VariantSet.organization_id == org_id).delete()
        total += self.db.query(VendorOrder).filter(VendorOrder.organization_id == org_id).delete()
        total += self.db.query(Plate).filter(Plate.organization_id == org_id).delete()
        total += self.db.query(MarkerPosition).filter(MarkerPosition.organization_id == org_id).delete()
        total += self.db.query(LinkageGroup).filter(LinkageGroup.organization_id == org_id).delete()
        total += self.db.query(GenomeMap).filter(GenomeMap.organization_id == org_id).delete()
        total += self.db.query(Reference).filter(Reference.organization_id == org_id).delete()
        total += self.db.query(ReferenceSet).filter(ReferenceSet.organization_id == org_id).delete()
        
        self.db.commit()
        return total
