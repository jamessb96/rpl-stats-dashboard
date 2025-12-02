# supabase_client.py
from supabase import create_client, Client
import pandas as pd

# 👉 Use YOUR project URL + anon key here
SUPABASE_URL = "https://uqdshubrtmisjsignyvv.supabase.co"
SUPABASE_ANON_KEY = SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVxZHNodWJydG1pc2pzaWdueXZ2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjQzNzY2MzcsImV4cCI6MjA3OTk1MjYzN30.WiOJuVuahGXRJ4FEeAbiX4SxPbu_Yq9v1-Ba5S7hdZ4"
  # your REAL anon key here

# Create Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

def get_leads_df() -> pd.DataFrame:
    """
    Returns the 'leads' table from Supabase as a pandas DataFrame.
    """
    response = (
        supabase.table("leads")
        .select("*")
        .order("created", desc=True)
        .execute()
    )

    data = response.data or []
    return pd.DataFrame(data)
