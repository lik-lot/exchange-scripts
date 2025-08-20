package main

import (
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"sync"
	"time"
)

type ScriptResult struct {
	Name     string
	Success  bool
	Duration time.Duration
	Error    error
	Output   string
}

func runPythonScript(scriptPath string, wg *sync.WaitGroup, results chan<- ScriptResult) {
	defer wg.Done()

	start := time.Now()
	scriptName := filepath.Base(scriptPath)
	scriptName = strings.TrimSuffix(scriptName, ".py")

	fmt.Printf("🔄 Starting %s...\n", scriptName)
	fmt.Printf("📋 Output from %s:\n", scriptName)
	fmt.Println(strings.Repeat("-", 40))

	cmd := exec.Command("python3", scriptPath)
	cmd.Dir = filepath.Dir(scriptPath)
	
	// Stream output in real-time
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr

	err := cmd.Run()
	duration := time.Since(start)

	result := ScriptResult{
		Name:     scriptName,
		Success:  err == nil,
		Duration: duration,
		Error:    err,
		Output:   "",
	}

	fmt.Println(strings.Repeat("-", 40))
	if err == nil {
		fmt.Printf("✓ %s completed in %v\n", scriptName, duration)
	} else {
		fmt.Printf("✗ %s failed in %v: %v\n", scriptName, duration, err)
	}

	results <- result
}

func main() {
	scriptDir := "."
	if len(os.Args) > 1 {
		scriptDir = os.Args[1]
	}

	// Working exchanges (17 total) - verified with TradingView
	pythonScripts := []string{
		//"bitmart.py",   // VERIFIED: BITMART exchange, keep_original format
		"bitrue.py", // VERIFIED: BITRUE exchange, keep_original format
		"btse.py",   // VERIFIED: BTSE exchange, remove_dash format
		"bybit.py",  // VERIFIED: BYBIT exchange, keep_original format
		//"coinbase.py",  // VERIFIED: COINBASE exchange, remove_dash format
		"coinex.py",    // VERIFIED: COINEX exchange, keep_original format
		"coinw.py",     // VERIFIED: COINW exchange, keep_original format
		"cryptocom.py", // VERIFIED: CRYPTOCOM exchange, keep_original format
		"gateio.py",    // VERIFIED: GATEIO exchange, keep_original format
		"gemini.py",    // VERIFIED: GEMINI exchange, keep_original format
		"htx.py",       // VERIFIED: HTX exchange, keep_original format
		//"kraken.py",    // VERIFIED: KRAKEN exchange, keep_original format
		"kucoin.py", // VERIFIED: KUCOIN exchange, remove_dash format
		"mexc.py",   // VERIFIED: MEXC exchange, keep_original format
		//"okx.py",       // VERIFIED: OKX exchange, remove_dash format
		"whitebit.py", // VERIFIED: WHITEBIT exchange, keep_original format

		// SKIPPED: Not available on TradingView (8 exchanges)
		// "biconomy.py",      // Not available on TradingView
		// "bigone.py",        // Not available on TradingView
		// "deepcoin.py",      // Not available on TradingView
		// "digifinex.py",     // Not available on TradingView
		// "hashkeyglobal.py", // Not available on TradingView
		// "lbank.py",         // Not available on TradingView
		// "pionex.py",        // Not available on TradingView
		// "toobit.py",        // Not available on TradingView
	}

	validScripts := []string{}
	for _, script := range pythonScripts {
		scriptPath := filepath.Join(scriptDir, script)
		if _, err := os.Stat(scriptPath); os.IsNotExist(err) {
			fmt.Printf("⚠ Skipping %s (file not found)\n", script)
			continue
		}
		validScripts = append(validScripts, script)
	}

	fmt.Printf("Starting parallel execution of %d verified working Python scripts...\n", len(validScripts))
	fmt.Println("=" + strings.Repeat("=", 60))

	var wg sync.WaitGroup
	results := make(chan ScriptResult, len(validScripts))

	startTime := time.Now()

	for _, script := range validScripts {
		scriptPath := filepath.Join(scriptDir, script)
		wg.Add(1)
		go runPythonScript(scriptPath, &wg, results)
	}

	wg.Wait()
	close(results)

	// Collect results
	var scriptResults []ScriptResult
	for result := range results {
		scriptResults = append(scriptResults, result)
	}

	totalDuration := time.Since(startTime)

	fmt.Println("\n" + strings.Repeat("=", 60))
	fmt.Printf("Execution Summary (Total time: %v)\n", totalDuration)
	fmt.Println(strings.Repeat("=", 60))

	successful := 0
	failed := 0
	var failedScripts []ScriptResult

	for _, result := range scriptResults {
		if result.Success {
			fmt.Printf("✓ %-15s - %v\n", result.Name, result.Duration)
			successful++
		} else {
			fmt.Printf("✗ %-15s - %v (ERROR)\n", result.Name, result.Duration)
			failedScripts = append(failedScripts, result)
			failed++
		}
	}

	fmt.Println(strings.Repeat("-", 60))
	fmt.Printf("Results: %d successful, %d failed\n", successful, failed)

	if len(failedScripts) > 0 {
		fmt.Println("\nFailed Scripts Details:")
		fmt.Println(strings.Repeat("-", 60))
		for _, result := range failedScripts {
			fmt.Printf("\n%s:\n", result.Name)
			fmt.Printf("Error: %v\n", result.Error)
			if len(result.Output) > 0 {
				fmt.Printf("Output:\n%s\n", result.Output)
			}
		}
	}

	if failed > 0 {
		os.Exit(1)
	}
}
