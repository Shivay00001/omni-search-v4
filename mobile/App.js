import React, { useState } from 'react';
import {
    StyleSheet, Text, View, TextInput, TouchableOpacity,
    ScrollView, SafeAreaView, ActivityIndicator, Linking
} from 'react-native';
import { StatusBar } from 'expo-status-bar';
import { Search, Globe, ArrowUp, Zap, BookOpen } from 'lucide-react-native';
import axios from 'axios';

const API_BASE = 'http://localhost:8000'; // Note: For physical devices, use your computer's IP

export default function App() {
    const [query, setQuery] = useState('');
    const [isSearching, setIsSearching] = useState(false);
    const [summary, setSummary] = useState('');
    const [sources, setSources] = useState([]);

    const handleSearch = async () => {
        if (!query.trim() || isSearching) return;

        setIsSearching(true);
        setSummary('');
        setSources([]);

        try {
            // Parallel fetch for sources
            axios.get(`${API_BASE}/test_search?q=${encodeURIComponent(query)}`)
                .then(res => setSources(res.data))
                .catch(err => console.log("Sources error", err));

            const res = await axios.post(`${API_BASE}/search`, { query, stream: false });
            setSummary(res.data.summary || res.data);

        } catch (error) {
            console.log(error);
            setSummary('Failed to connect to Omni backend. Ensure the server is running on your network.');
        } finally {
            setIsSearching(false);
        }
    };

    return (
        <SafeAreaView style={styles.container}>
            <StatusBar style="light" />

            <View style={styles.header}>
                <Text style={styles.logo}>Omni</Text>
            </View>

            <ScrollView contentContainerStyle={styles.scrollContent}>
                {!summary && !isSearching && (
                    <View style={styles.hero}>
                        <Text style={styles.heroText}>Where knowledge begins.</Text>
                    </View>
                )}

                {summary ? (
                    <View style={styles.resultContainer}>
                        <View style={styles.sectionHeader}>
                            <Zap size={18} color="#3b82f6" fill="#3b82f6" />
                            <Text style={styles.sectionTitle}>Answer</Text>
                        </View>
                        <Text style={styles.summaryText}>{summary}</Text>

                        {sources.length > 0 && (
                            <View style={{ marginTop: 24 }}>
                                <View style={styles.sectionHeader}>
                                    <BookOpen size={18} color="#94a3b8" />
                                    <Text style={styles.sectionTitle}>Sources</Text>
                                </View>
                                {sources.map((source, i) => (
                                    <TouchableOpacity
                                        key={i}
                                        style={styles.sourceCard}
                                        onPress={() => Linking.openURL(source.url)}
                                    >
                                        <Text style={styles.sourceTitle} numberOfLines={1}>{source.title}</Text>
                                        <Text style={styles.sourceUrl}>{new URL(source.url).hostname}</Text>
                                    </TouchableOpacity>
                                ))}
                            </View>
                        )}
                    </View>
                ) : null}

                {isSearching && !summary && (
                    <View style={styles.loaderContainer}>
                        <ActivityIndicator size="large" color="#3b82f6" />
                        <Text style={styles.loaderText}>Synthesizing...</Text>
                    </View>
                )}
            </ScrollView>

            {/* Persistent Search Input */}
            <View style={styles.searchBarContainer}>
                <View style={styles.searchBar}>
                    <Search color="#94a3b8" size={20} />
                    <TextInput
                        style={styles.input}
                        placeholder="Ask anything..."
                        placeholderTextColor="#94a3b8"
                        value={query}
                        onChangeText={setQuery}
                        onSubmitEditing={handleSearch}
                    />
                    <TouchableOpacity
                        style={[styles.sendButton, { backgroundColor: query.trim() ? '#3b82f6' : '#222' }]}
                        onPress={handleSearch}
                    >
                        <ArrowUp color="white" size={20} />
                    </TouchableOpacity>
                </View>
            </View>
        </SafeAreaView>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: '#0A0A0B',
    },
    header: {
        paddingHorizontal: 20,
        paddingVertical: 15,
    },
    logo: {
        fontSize: 24,
        fontWeight: '800',
        color: '#3b82f6',
    },
    scrollContent: {
        paddingHorizontal: 20,
        paddingBottom: 100,
    },
    hero: {
        marginTop: 100,
        alignItems: 'center',
    },
    heroText: {
        fontSize: 32,
        fontWeight: '800',
        color: 'white',
        textAlign: 'center',
    },
    searchBarContainer: {
        position: 'absolute',
        bottom: 20,
        left: 0,
        right: 0,
        paddingHorizontal: 20,
    },
    searchBar: {
        flexDirection: 'row',
        alignItems: 'center',
        backgroundColor: '#111113',
        borderRadius: 15,
        paddingHorizontal: 12,
        paddingVertical: 8,
        borderWidth: 1,
        borderColor: 'rgba(255,255,255,0.1)',
    },
    input: {
        flex: 1,
        color: 'white',
        fontSize: 16,
        marginLeft: 10,
        paddingVertical: 10,
    },
    sendButton: {
        borderRadius: 10,
        padding: 8,
    },
    resultContainer: {
        marginTop: 20,
    },
    sectionHeader: {
        flexDirection: 'row',
        alignItems: 'center',
        marginBottom: 12,
        gap: 8,
    },
    sectionTitle: {
        fontSize: 16,
        fontWeight: '700',
        color: 'white',
        textTransform: 'uppercase',
    },
    summaryText: {
        color: '#e2e8f0',
        fontSize: 17,
        lineHeight: 26,
    },
    sourceCard: {
        backgroundColor: 'rgba(255,255,255,0.03)',
        borderRadius: 12,
        padding: 15,
        marginBottom: 10,
        borderWidth: 1,
        borderColor: 'rgba(255,255,255,0.05)',
    },
    sourceTitle: {
        color: 'white',
        fontSize: 14,
        fontWeight: '600',
    },
    sourceUrl: {
        color: '#94a3b8',
        fontSize: 12,
        marginTop: 4,
    },
    loaderContainer: {
        marginTop: 50,
        alignItems: 'center',
    },
    loaderText: {
        color: '#94a3b8',
        marginTop: 10,
    }
});
