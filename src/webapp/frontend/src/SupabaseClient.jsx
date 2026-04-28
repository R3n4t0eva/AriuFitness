import { createClient } from '@supabase/supabase-js';

const supabaseUrl = 'https://czrztgsqpbijesiuwhnw.supabase.co';
const supabaseAnonKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImN6cnp0Z3NxcGJpamVzaXV3aG53Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzY5ODI5NjEsImV4cCI6MjA5MjU1ODk2MX0.U4HntAfDPxUqg9CIXKjbSj2W_igYhijIQoaI1l9UwV0';

// Esporti la costante 'supabase' già inizializzata
export const supabase = createClient(supabaseUrl, supabaseAnonKey);