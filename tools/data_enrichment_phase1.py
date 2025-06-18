#!/usr/bin/env python3
"""
Data Enrichment Phase 1: Immediate Contact Database Improvements

This script performs immediate data quality improvements on the 191 contact records:
1. Extract names from email addresses
2. Generate unique Contact IDs
3. Standardize Date Added fields
4. Classify Lead Sources
5. Basic Contact Type classification

Usage: python3 tools/data_enrichment_phase1.py
"""

import os
import re
import asyncio
from datetime import datetime
from dotenv import load_dotenv
from notion_client import Client
import time

# Load environment variables
load_dotenv()

class ContactEnrichmentService:
    def __init__(self):
        self.notion = Client(auth=os.getenv('NOTION_API_KEY'))
        self.contacts_db_id = os.getenv('NOTION_CONTACTS_PROFILES_DB')
        self.processed_count = 0
        self.error_count = 0
        
    def extract_name_from_email(self, email):
        """Extract potential names from email addresses using pattern recognition"""
        if not email:
            return {'first_name': '', 'last_name': ''}
            
        local_part = email.split('@')[0].lower()
        
        # Remove numbers and common prefixes/suffixes
        cleaned = re.sub(r'\d+', '', local_part)
        cleaned = re.sub(r'^(info|admin|contact|hello|hi)', '', cleaned)
        cleaned = re.sub(r'(info|admin|contact)$', '', cleaned)
        
        # Common patterns for name extraction
        patterns = [
            r'([a-zA-Z]{2,})\.([a-zA-Z]{2,})',      # firstname.lastname
            r'([a-zA-Z]{2,})_([a-zA-Z]{2,})',       # firstname_lastname
            r'([a-zA-Z]{2,})-([a-zA-Z]{2,})',       # firstname-lastname
            r'([a-zA-Z]{2,})([a-zA-Z]{2,})',        # firstnamelastname (if reasonable length)
        ]
        
        for pattern in patterns:
            match = re.match(pattern, cleaned)
            if match:
                first = match.group(1).title()
                last = match.group(2).title()
                
                # Validate reasonable name lengths
                if 2 <= len(first) <= 15 and 2 <= len(last) <= 15:
                    return {'first_name': first, 'last_name': last}
        
        # Fallback: use the cleaned local part as first name
        if 2 <= len(cleaned) <= 20:
            return {'first_name': cleaned.title(), 'last_name': ''}
        
        return {'first_name': '', 'last_name': ''}
    
    def generate_contact_id(self, email, index):
        """Generate unique contact identifiers"""
        if not email:
            return f"CONTACT-UNKNOWN-{str(index).zfill(4)}"
            
        domain = email.split('@')[1].split('.')[0].upper()
        return f"CONTACT-{domain}-{str(index).zfill(4)}"
    
    def classify_lead_source(self, email):
        """Classify lead source based on email domain patterns"""
        if not email:
            return 'Website'
            
        domain = email.split('@')[1].lower()
        
        # Educational institutions
        if domain.endswith('.edu'):
            return 'Event'
        
        # Business domains
        business_indicators = ['corp', 'inc', 'llc', 'ltd', 'company', 'consulting', 'studio']
        if any(indicator in domain for indicator in business_indicators):
            return 'Referral'
        
        # Common personal email providers
        personal_domains = ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com', 'aol.com']
        if domain in personal_domains:
            return 'Website'
        
        # Art/creative domains
        art_indicators = ['art', 'gallery', 'studio', 'creative', 'design']
        if any(indicator in domain for indicator in art_indicators):
            return 'Event'
        
        return 'Website'  # Default
    
    def classify_contact_type(self, email):
        """Classify contact type based on email patterns"""
        if not email:
            return []
            
        domain = email.split('@')[1].lower()
        local_part = email.split('@')[0].lower()
        
        contact_types = []
        
        # The 7 Space specific patterns
        art_keywords = ['art', 'gallery', 'studio', 'creative', 'design', 'artist', 'curator']
        if any(keyword in domain or keyword in local_part for keyword in art_keywords):
            contact_types.extend(['Artist', 'Gallery Contact'])
        
        # AM Consulting specific patterns
        business_keywords = ['consulting', 'business', 'corp', 'inc', 'llc', 'ceo', 'manager', 'director']
        if any(keyword in domain or keyword in local_part for keyword in business_keywords):
            contact_types.extend(['Business Contact', 'Potential Client'])
        
        # Educational institutions
        if domain.endswith('.edu'):
            contact_types.append('Academic Contact')
        
        # Media and press
        media_keywords = ['media', 'press', 'news', 'journalist', 'reporter']
        if any(keyword in domain or keyword in local_part for keyword in media_keywords):
            contact_types.append('Media Contact')
        
        # Default if no specific classification
        if not contact_types:
            contact_types = ['General Contact']
        
        return contact_types
    
    async def get_all_contacts(self):
        """Retrieve all contacts from the database with pagination"""
        all_contacts = []
        has_more = True
        next_cursor = None
        
        print("📥 Fetching all contact records...")
        
        while has_more:
            try:
                if next_cursor:
                    response = self.notion.databases.query(
                        database_id=self.contacts_db_id,
                        start_cursor=next_cursor,
                        page_size=100
                    )
                else:
                    response = self.notion.databases.query(
                        database_id=self.contacts_db_id,
                        page_size=100
                    )
                
                all_contacts.extend(response['results'])
                has_more = response['has_more']
                next_cursor = response.get('next_cursor')
                
                print(f"   ├─ Fetched {len(response['results'])} records (Total: {len(all_contacts)})")
                
            except Exception as e:
                print(f"❌ Error fetching contacts: {e}")
                break
        
        print(f"✅ Retrieved {len(all_contacts)} total contacts")
        return all_contacts
    
    async def enrich_contact(self, contact, index):
        """Enrich a single contact record"""
        try:
            contact_id = contact['id']
            properties = contact.get('properties', {})
            
            # Get email address
            email_prop = properties.get('Email', {})
            email = email_prop.get('email', '') if email_prop else ''
            
            if not email:
                print(f"   ⚠️  Record {index}: No email address, skipping")
                return False
            
            # Prepare updates
            updates = {}
            
            # 1. Extract and set names if not already present
            first_name_prop = properties.get('First Name', {})
            current_first_name = ''
            if first_name_prop.get('title'):
                current_first_name = first_name_prop['title'][0]['text']['content'] if first_name_prop['title'] else ''
            
            if not current_first_name or current_first_name.lower() in ['untitled', '']:
                names = self.extract_name_from_email(email)
                if names['first_name']:
                    updates['First Name'] = {
                        'title': [{'text': {'content': names['first_name']}}]
                    }
                if names['last_name']:
                    updates['Last Name'] = {
                        'rich_text': [{'text': {'content': names['last_name']}}]
                    }
            
            # 2. Generate Contact ID if not present
            contact_id_prop = properties.get('Contact ID', {})
            current_contact_id = ''
            if contact_id_prop.get('rich_text'):
                current_contact_id = contact_id_prop['rich_text'][0]['text']['content'] if contact_id_prop['rich_text'] else ''
            
            if not current_contact_id:
                new_contact_id = self.generate_contact_id(email, index)
                updates['Contact ID'] = {
                    'rich_text': [{'text': {'content': new_contact_id}}]
                }
            
            # 3. Set Date Added if not present
            date_added_prop = properties.get('Date Added', {})
            if not date_added_prop.get('date'):
                updates['Date Added'] = {
                    'date': {'start': datetime.now().isoformat()[:10]}
                }
            
            # 4. Classify Lead Source if not present
            lead_source_prop = properties.get('Lead Source', {})
            if not lead_source_prop.get('select'):
                lead_source = self.classify_lead_source(email)
                updates['Lead Source'] = {
                    'select': {'name': lead_source}
                }
            
            # 5. Set Contact Type if not present
            contact_type_prop = properties.get('Contact Type', {})
            if not contact_type_prop.get('multi_select'):
                contact_types = self.classify_contact_type(email)
                if contact_types:
                    updates['Contact Type'] = {
                        'multi_select': [{'name': ct} for ct in contact_types]
                    }
            
            # Apply updates if any
            if updates:
                self.notion.pages.update(page_id=contact_id, properties=updates)
                print(f"   ✅ Record {index}: Updated {len(updates)} fields for {email}")
                self.processed_count += 1
                return True
            else:
                print(f"   ℹ️  Record {index}: No updates needed for {email}")
                return True
                
        except Exception as e:
            print(f"   ❌ Record {index}: Error processing {email}: {e}")
            self.error_count += 1
            return False
    
    async def run_enrichment(self):
        """Run the complete enrichment process"""
        print("🚀 STARTING PHASE 1 DATA ENRICHMENT")
        print("=" * 60)
        
        start_time = time.time()
        
        # Get all contacts
        contacts = await self.get_all_contacts()
        
        if not contacts:
            print("❌ No contacts found to process")
            return
        
        print(f"\n📊 Processing {len(contacts)} contact records...")
        print("=" * 60)
        
        # Process each contact
        for index, contact in enumerate(contacts, 1):
            await self.enrich_contact(contact, index)
            
            # Rate limiting - pause every 10 requests
            if index % 10 == 0:
                print(f"   ⏸️  Processed {index}/{len(contacts)} - Pausing for rate limiting...")
                time.sleep(1)
        
        # Final summary
        end_time = time.time()
        duration = end_time - start_time
        
        print("\n" + "=" * 60)
        print("🎉 PHASE 1 ENRICHMENT COMPLETE")
        print("=" * 60)
        print(f"📊 Total Records: {len(contacts)}")
        print(f"✅ Successfully Processed: {self.processed_count}")
        print(f"❌ Errors: {self.error_count}")
        print(f"⏱️  Duration: {duration:.2f} seconds")
        print(f"📈 Success Rate: {(self.processed_count/len(contacts)*100):.1f}%")
        
        if self.processed_count > 0:
            print("\n🎯 IMPROVEMENTS MADE:")
            print("   ├─ Names extracted from email addresses")
            print("   ├─ Unique Contact IDs generated")
            print("   ├─ Date Added fields standardized")
            print("   ├─ Lead Sources classified")
            print("   └─ Contact Types categorized")
            
            print("\n🚀 NEXT STEPS:")
            print("   ├─ Review enriched data in Notion")
            print("   ├─ Run Phase 2 enrichment (server-side automation)")
            print("   └─ Activate workflow automation with improved data")

async def main():
    """Main execution function"""
    enrichment_service = ContactEnrichmentService()
    await enrichment_service.run_enrichment()

if __name__ == "__main__":
    asyncio.run(main())
