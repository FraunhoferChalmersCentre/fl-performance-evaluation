import benchmark_C100
import benchmark_C100_old
import benchmark_coop


def main():
    benchmark_C100.bench(False)
    benchmark_C100_old.bench(False)
    benchmark_coop.bench(False)


if __name__ == '__main__':
    main()
