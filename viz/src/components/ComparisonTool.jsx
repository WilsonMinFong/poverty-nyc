import React, { useState } from 'react';

const ComparisonTool = ({ povertyData, rentData, onExit, onVisualize }) => {
    const [step, setStep] = useState('input'); // 'input' or 'results'
    const [formData, setFormData] = useState({
        zipCode: '',
        income: '',
        rent: ''
    });
    const [error, setError] = useState('');

    const handleSubmit = (e) => {
        e.preventDefault();
        setError('');

        // Validate Zip Code exists in data
        const povertyFeature = povertyData?.features.find(f => f.properties.zip_code === formData.zipCode);
        const rentFeature = rentData?.features.find(f => f.properties.zip_code === formData.zipCode);

        if (!povertyFeature || !rentFeature) {
            setError('Zip code not found in our database (NYC only).');
            return;
        }

        // Trigger map flyTo
        if (onVisualize) {
            onVisualize(formData.zipCode);
        }

        setStep('results');
    };

    const formatCurrency = (val) => {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD',
            maximumSignificantDigits: 3
        }).format(val);
    };

    const renderInput = () => (
        <div style={{
            background: 'white',
            padding: '30px',
            borderRadius: '12px',
            boxShadow: '0 4px 20px rgba(0,0,0,0.2)',
            maxWidth: '400px',
            width: '100%',
            margin: '0 auto'
        }}>
            <h2 style={{ marginTop: 0, color: '#2c3e50' }}>Compare Yourself</h2>
            <p style={{ color: '#666', marginBottom: '20px' }}>
                See how your income and rent compare to your neighborhood averages.
            </p>

            <form onSubmit={handleSubmit}>
                <div style={{ marginBottom: '15px' }}>
                    <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold', color: '#333' }}>Zip Code</label>
                    <input
                        type="text"
                        value={formData.zipCode}
                        onChange={(e) => setFormData({ ...formData, zipCode: e.target.value })}
                        placeholder="e.g. 10001"
                        style={{ width: '100%', padding: '10px', borderRadius: '4px', border: '1px solid #ddd', fontSize: '16px', boxSizing: 'border-box' }}
                        required
                    />
                </div>

                <div style={{ marginBottom: '15px' }}>
                    <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold', color: '#333' }}>Annual Household Income</label>
                    <input
                        type="number"
                        value={formData.income}
                        onChange={(e) => setFormData({ ...formData, income: e.target.value })}
                        placeholder="e.g. 75000"
                        style={{ width: '100%', padding: '10px', borderRadius: '4px', border: '1px solid #ddd', fontSize: '16px', boxSizing: 'border-box' }}
                        required
                    />
                </div>

                <div style={{ marginBottom: '20px' }}>
                    <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold', color: '#333' }}>Monthly Rent</label>
                    <input
                        type="number"
                        value={formData.rent}
                        onChange={(e) => setFormData({ ...formData, rent: e.target.value })}
                        placeholder="e.g. 2500"
                        style={{ width: '100%', padding: '10px', borderRadius: '4px', border: '1px solid #ddd', fontSize: '16px', boxSizing: 'border-box' }}
                        required
                    />
                </div>

                {error && <div style={{ color: '#d32f2f', marginBottom: '15px' }}>{error}</div>}

                <div style={{ display: 'flex', gap: '10px' }}>
                    <button
                        type="button"
                        onClick={onExit}
                        style={{ flex: 1, padding: '12px', background: '#f5f5f5', border: 'none', borderRadius: '4px', cursor: 'pointer', color: '#333' }}
                    >
                        Cancel
                    </button>
                    <button
                        type="submit"
                        style={{ flex: 1, padding: '12px', background: '#2c3e50', border: 'none', borderRadius: '4px', cursor: 'pointer', color: 'white', fontWeight: 'bold' }}
                    >
                        Compare
                    </button>
                </div>
            </form>
        </div>
    );

    const renderResults = () => {
        const povertyFeature = povertyData?.features.find(f => f.properties.zip_code === formData.zipCode);
        const rentFeature = rentData?.features.find(f => f.properties.zip_code === formData.zipCode);

        const neighborhoodIncome = povertyFeature?.properties.median_household_income || 0;
        const neighborhoodRent = rentFeature?.properties.rent_index || 0;

        const userIncome = parseFloat(formData.income);
        const userRent = parseFloat(formData.rent);

        const incomeRatio = (userIncome / neighborhoodIncome) * 100;
        const rentDiff = userRent - neighborhoodRent;

        const userBurden = ((userRent * 12) / userIncome) * 100;
        const neighborhoodBurden = ((neighborhoodRent * 12) / neighborhoodIncome) * 100;

        return (
            <div style={{
                background: 'white',
                padding: '30px',
                borderRadius: '12px',
                boxShadow: '0 4px 20px rgba(0,0,0,0.2)',
                maxWidth: '400px',
                width: '100%',
                margin: '0 auto'
            }}>
                <h2 style={{ marginTop: 0, color: '#2c3e50', borderBottom: '1px solid #eee', paddingBottom: '10px' }}>
                    Results: {formData.zipCode}
                </h2>

                <div style={{ marginBottom: '20px' }}>
                    <h3 style={{ fontSize: '1em', color: '#666', marginBottom: '5px' }}>Income Comparison</h3>
                    <div style={{ fontSize: '1.2em', fontWeight: 'bold', color: incomeRatio >= 100 ? '#388e3c' : '#f57c00' }}>
                        You earn {incomeRatio.toFixed(0)}% of the median.
                    </div>
                    <div style={{ fontSize: '0.9em', color: '#888' }}>
                        You: {formatCurrency(userIncome)} vs. Neighborhood: {formatCurrency(neighborhoodIncome)}
                    </div>
                </div>

                <div style={{ marginBottom: '20px' }}>
                    <h3 style={{ fontSize: '1em', color: '#666', marginBottom: '5px' }}>Rent Comparison</h3>
                    <div style={{ fontSize: '1.2em', fontWeight: 'bold', color: rentDiff > 0 ? '#d32f2f' : '#388e3c' }}>
                        Your rent is {rentDiff > 0 ? formatCurrency(rentDiff) + ' higher' : formatCurrency(Math.abs(rentDiff)) + ' lower'} than market.
                    </div>
                    <div style={{ fontSize: '0.9em', color: '#888' }}>
                        You: {formatCurrency(userRent)} vs. Market: {formatCurrency(neighborhoodRent)}
                    </div>
                </div>

                <div style={{ marginBottom: '20px' }}>
                    <h3 style={{ fontSize: '1em', color: '#666', marginBottom: '5px' }}>Rent Burden</h3>
                    <div style={{ fontSize: '1.2em', fontWeight: 'bold', color: userBurden > 30 ? '#d32f2f' : '#388e3c' }}>
                        You spend {userBurden.toFixed(1)}% on rent.
                    </div>
                    <div style={{ fontSize: '0.9em', color: '#888' }}>
                        Neighborhood Avg (New Tenants): {neighborhoodBurden.toFixed(1)}%
                    </div>
                </div>

                <button
                    onClick={() => setStep('input')}
                    style={{ width: '100%', padding: '12px', background: '#f5f5f5', border: 'none', borderRadius: '4px', cursor: 'pointer', color: '#333', marginBottom: '10px' }}
                >
                    Check Another Zip
                </button>
                <button
                    onClick={onExit}
                    style={{ width: '100%', padding: '12px', background: '#2c3e50', border: 'none', borderRadius: '4px', cursor: 'pointer', color: 'white' }}
                >
                    Close
                </button>
            </div>
        );
    };

    return (
        <div style={{
            position: 'fixed',
            top: 0,
            left: 0,
            width: '100vw',
            height: '100vh',
            background: 'rgba(0,0,0,0.5)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000
        }}>
            {step === 'input' ? renderInput() : renderResults()}
        </div>
    );
};

export default ComparisonTool;
